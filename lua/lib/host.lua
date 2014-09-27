--[==[

Management features for hosting via the bot

Creating the commands:
!def -a=user,hours host local host = require("host"); return host.host(user,
 hours)

Usage:
!host lietu
!host lietu 3

Hosting will automatically be cancelled after a number of hours that can be
specified as an argument, defaults to 10 hours.

--]==]

local chat = require("chat")
local utils = require("utils")
local host = {}

host.defaultHours = 10
host.cancelUnhost = nil

--- Issue command to host a user
-- @param user The username
-- @return nil
function host._host(user)
    chat.message(".host " .. user)
end

--- Unhost the currently hosted user
-- @return nil
function host.unhost()
    chat.message(".unhost")
end

--- Host a user for the given amount of hours
-- @param user The username
-- @param hours Number of hours to host
-- @return nil
function host.host(user, hours)
    if hours == nil then
        hours = host.defaultHours
    end

    if host.cancelUnhost ~= nil then
        host.cancelUnhost()
    end

    local function unhost()
        chat.message("Unhosting " .. user .. " after " .. hours .. " hours")
        host.unhost()
    end

    host._host(user)
    host.cancelUnhost = utils.delayed(hours * 3600, unhost)

    return user .. " is now being hosted for the next " .. hours .. " hours"
end

return host
