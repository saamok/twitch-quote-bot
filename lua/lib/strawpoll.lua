--[==[

Strawpoll API

Create new Strawpolls via your chat.

You can add a command to create new strawpolls, e.g.:
!def -ul=mod -a=title,... poll local sp = require("strawpoll"); return sp.create(title, unpack(arg))


--]==]

local http = require("http")
local json = require("dkjson")

local strawpoll = {}

-- Basic configuration for Strawpoll API
strawpoll.host = "strawpoll.me"
strawpoll.url = "http://strawpoll.me/ajax/new-poll"
strawpoll.pollBaseUrl = "http://strawpoll.me/"
strawpoll.contentType = "application/x-www-form-urlencoded; charset=UTF-8"

--- Create a Strawpoll with the given settings
-- @param title The poll title
-- @param multi If it should allow multiple answers
-- @param permissive Allow multiple votes from the same IP
-- @param options List of the poll options
--
function _create_internal(title, multi, permissive, options)
    local data = http.data()
    data.add("title", title)

    for i, option in pairs(options) do
        data.add("options[]", tostring(option))
    end

    data.add("multi", tostring(multi))
    data.add("permissive", tostring(permissive))

    local headers = http.data()
    headers.add("Host", strawpoll.host)
    headers.add("Content-Type", strawpoll.contentType)
    headers.add("X-Requested-With", "XMLHttpRequest")
    headers.add("Accept", "*/*")

    local response_json = http.post(strawpoll.url, data, headers)
    local response = json.decode(response_json)

    return strawpoll.pollBaseUrl .. response.id
end

--- Create a simple poll
-- @param title The poll title
-- @param ... Any number of options
--
function strawpoll.create(title, ...)
    local options = {}
    for k, option in pairs(arg) do
        if k ~= "n" then
            options[k] = option
        end
    end

    return _create_internal(title, false, false, options)
end

return strawpoll