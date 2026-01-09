def filter(event)
    if (@last_date == event.timestamp)
        new_timestamp = LogStash::Timestamp.at((event.timestamp+@n))
        event.timestamp=new_timestamp
        if (@n<0.999999999)
            @n+=(1/1000000000.0)
        else
            @n=(1/1000000000.0)
        end
    else
        @last_date= event.timestamp
        @n=(1/1000000000.0)
    end
    return [event]
end
