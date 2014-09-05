local http = require("http")
local json = require("dkjson")

local twitch = {}

twitch.apiUrl = "https://api.twitch.tv/kraken/"
twitch.accept = "application/vnc.twitchtv.v2+json"

--- Get the current game for the given streamer
-- @param user
--
function twitch.game(user)
    local url = twitch.apiUrl .. "streams/" .. user

    local headers = http.data()
    headers.add("Accept", twitch.accept)

    local json_data = http.get(url, nil, headers)
    local data = json.decode(json_data)

    return data.stream.game
end

--- Get the current viewer count for the given streamer
-- @param user
--
function twitch.viewers(user)
    local url = twitch.apiUrl .. "streams/" .. user

    local headers = http.data()
    headers.add("Accept", twitch.accept)

    local json_data = http.get(url, nil, headers)
    local data = json.decode(json_data)

    return data.stream.viewers
end

--- Get the current follower count for the given streamer
-- @param user
--
function twitch.followers(user)
    local url = twitch.apiUrl .. "streams/" .. user

    local headers = http.data()
    headers.add("Accept", twitch.accept)

    local json_data = http.get(url, nil, headers)
    local data = json.decode(json_data)

    return data.stream.channel.followers
end

return twitch