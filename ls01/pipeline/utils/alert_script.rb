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
configurationFile = "/usr/share/logstash/pipeline/utils/alert_config.json"
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
  recipients.each do |recipientAddress|
    messageHeader = ""
    messageHeader << "From: <#{@senderAddress}>\r\n"
    messageHeader << "To: <#{recipientAddress}>\r\n"
    messageHeader << "Subject: #{subject}\r\n"
    message = messageHeader + "\r\n" + messageBody + "\r\n"

    smtp = Net::SMTP.new @smtp_server, @port
    smtp.start() do |smtp|
      smtp.send_message message, @senderAddress, recipientAddress
    end
  end
end

#create a mesagge with event fields
def composeMessage(event)
  timestamp = (DateTime.parse(event.timestamp.to_s).new_offset("#{@tz}").iso8601(9)).to_s
  messageBody ="This is an automatic notification from TED to report the activation of an alarm, the details are: "+"\n\n"+ "Subsystem: " + event.get("subsystem") + "\n" + "Timestamp: " + timestamp + "\n" + "Message: " + event.get("msg") + "\r\n"
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
  currentTime = Time.now().to_datetime.new_offset("#{@tz}").to_time
  if @timerDict[alert["expression"]].nil? || (currentTime - @timerDict[alert["expression"]]) >= toSeconds(@hours, @minutes)
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
      messageBody = composeMessage(event)
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
