local userdata = require("userdata")
local utils = require("utils")
local chat = require("chat")

-- The xp "class"
local xp = {}

local xp_currency = _G["settings"]["XP_CURRENCY"]
local ignore_users = utils.Set(utils.list_to_lua(
    _G["settings"]["IGNORE_USERS"]
))

-- How many seconds between gaining XP
local xp_seconds = 5 * 60

--- Get the given user's current XP
-- @param user
--
function xp.get_user_xp(user)
    local user_xp = userdata.get_value(xp_currency, user)

    if user_xp == nil then
        user_xp = 0
    end

    return user_xp
end

--- Update the given user's current XP
-- @param user
-- @param xp
--
function xp.set_user_xp(user, xp)
    userdata.set_value(xp_currency, user, xp)
    userdata.save_highscore(xp_currency, user, xp)
end

--- Function run periodically to increase user XP
--
function xp.tick()
    local users = chat.get_users()
    local given_xp = 0

    for key, user in pairs(users) do
        if not ignore_users[user] then
            xp.set_user_xp(user, xp.get_user_xp(user) + 1)
            given_xp = given_xp + 1
        else
            _G["log"]("Ignoring user " .. user)
        end
    end
end

--- Get a chat message about the user's current XP level
-- @param user
--
function xp.get_xp(user)
    local user_xp = xp.get_user_xp(user)

    return user .. ", you currently have " .. user_xp .." " .. xp_currency
end

--- Initialize XP timer
--
function xp.init()
    utils.interval(xp_seconds, function() xp.tick() end)
end

return xp