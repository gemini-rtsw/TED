require "json"
require "net/smtp"
require "date"

#define email varible
@smtp_server = "smtp.cl.gemini.edu"
@port = 25
@senderAddress = "TED-ALARM@noirlab.edu"

#define slack variable
@channel = "ruby-alert-bot"
@username = "#ruby-bot"
@slackWebhook = "https://hooks.slack.com/services/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"

#timezone
@tz = `date "+%Z"`.strip

#timer for send alerts (hours,minutes)
@hours = 2
@minutes = 30
@timerDict = {}
@timerFile = "./timerAlerts.txt"

#read the .json file and set the content to alerts
configurationFile = "/usr/share/logstash/utils/alert_config.json"
content = ""
open(configurationFile, "r") do |file|
  content = file.read()
end
@alerts = JSON.parse(content)

#slack config
def notifySlack(messageBody)
  payload = {
    :channel => "#{@channel}",
    :username => "#{@username}",
    :text => "#{messageBody}",
  }.to_json
  cmd = "curl -X POST --data-urlencode 'payload=#{payload}' #{@slackWebhook}"
  system(cmd)
end

#email config
def notifyEmail(recipients, subject, messageBody)
    messageHeader = ""
    messageHeader << "From: <#{@senderAddress}>\r\n"
    messageHeader << "To: <#{recipients.map{ |r| "#{r}" }.join(", ")}>\r\n"
    messageHeader << "Subject: #{subject}\r\n"
    messageHeader << "MIME-Version: 1.0\r\n"
    messageHeader << "Content-type: text/html\r\n"
    message = messageHeader + "\r\n" + messageBody + "\r\n"

    smtp = Net::SMTP.new @smtp_server, @port
    smtp.start() do |smtp|
      smtp.send_message message, @senderAddress, recipients
  end
end

#create a mesagge with event fields
def composeMessage(event, alertMessage)
  timestamp = (DateTime.parse(event.timestamp.to_s).new_offset("#{@tz}").iso8601(9)).to_s
  messageBody = <<-HTML
<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
        }
        .container {
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 5px;
            background-color: #f9f9f9;
        }
        .header {
            font-size: 20px;
            font-weight: bold;
            color: #333;
        }
        .content {
            margin-top: 20px;
        }
        .subsystem, .timestamp, .message {
            margin-bottom: 5px;
        }
        .alert {
            color: #d9534f;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">This is an automatic notification from TED to report the activation of an alarm</div>
        <div class="content">
            <div class="subsystem"><strong>Subsystem:</strong> #{event.get("subsystem")}</div>
            <div class="timestamp"><strong>Timestamp:</strong> #{timestamp}</div>
            <div class="message"><strong>Message:</strong> #{event.get("msg")}</div>
            <div class="alert">#{alertMessage}</div>
        </div>
    </div>
</body>
</html>
HTML
  return messageBody
end

#define flags for alerts
def flags(event, alert)
  return false if alert["exclude"].include?(event.get("subsystem"))
  return alert["source"] == "logstash" &&
           (event.get("subsystem") =~ /.*#{alert["subsystem"]}.*/) &&
           (event.get("msg") =~ /.*#{alert["expression"]}.*/)
end

#Timer funtion for avoid flood emails
def timer(event, alert)
  state = false
  interval= toSeconds(@hours, @minutes)
  if !alert["interval"].nil?
          interval = toSeconds(alert["interval"][0].to_i , alert["interval"][1].to_i )
  end
  currentTime = Time.now().to_datetime.new_offset("#{@tz}").to_time
  if @timerDict[alert["expression"]].nil? || (currentTime - @timerDict[alert["expression"]]) >= interval
    @timerDict[alert["expression"]] = currentTime
    writeTimer()
    state = true
  end
  return state
end

#read persistent timer dictionary
def readTimer()
  return unless File.exist?(@timerFile)

  File.foreach(@timerFile) do |line|
    key, value = line.strip.split("->")
    @timerDict[key] = Time.parse(value)
  end
end

#write persistent timer dictionary
def writeTimer()
  return if @timerDict.empty?

  File.open(@timerFile, "w") do |file|
    @timerDict.each do |key, value|
      file.puts "#{key}->#{value}"
    end
  end
end

#convert hours and minutes in seconds
def toSeconds(hours, minutes)
  seconds = (hours * 3600) + (minutes * 60)
  return seconds
end

#read funtion one time for instance?
readTimer()

#main funtion for logstash
def filter(event)
  for alert in @alerts
    if (flags(event, alert) && timer(event, alert))
      messageBody = composeMessage(event, alert["alertMessage"])
      alert["triggerAlarm"].map { |ta|
        case ta["service"]
        when "slack"
          notifySlack(messageBody)
        when "email"
          notifyEmail(ta["to"], alert["ruleName"], messageBody)
        else
          puts "service dosn't exist"
        end
      }
    end
  end
  return [event]
end

