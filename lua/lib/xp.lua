local datasource = require("datasource")
local utils = require("utils")
local chat = require("chat")

-- The xp "class"
local xp = {}

-- The in-memory XP database
local xp_data = {}

-- How many seconds between gaining XP
local xp_seconds = 5 * 60

--- Get the given user's current XP
-- @param user
--
function xp.get_user_xp(user)
    if xp_data[user] == nil then
        xp_data[user] = 0
    end

    return xp_data[user]
end

--- Update the given user's current XP
-- @param user
-- @param xp
--
function xp.set_user_xp(user, xp)
    xp_data[user] = xp
end

--- Function run periodically to increase user XP
--
function xp.tick()
    local users = chat.get_users()
    local user_xp
    local given_xp = 0

    for key, user in pairs(users) do
        xp.set_user_xp(user, xp.get_user_xp(user) + 1)
        given_xp = given_xp + 1
    end

    datasource.set("xp_data", xp_data)

    -- _G["log"]("XP update, gave away " .. given_xp .. " xp")
end

--- Initialize XP timer
--
function xp.init()
    xp_data = datasource.get("xp_data")
    if xp_data == nil then
        xp_data = {}
    end

    utils.interval(xp_seconds, function() xp.tick() end)
end

return xp