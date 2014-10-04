--[==[

User data container

Provide a consistent method for accessing user-specific data,
e.g. points or XP.

Example usage:

local chat = require("chat")
local userdata = require("userdata")
userdata.set_value("points", "lietu", 500)
chat.message("lietu has " .. userdata.get_value("points", "lietu") .. "points")

--]==]

local datasource = require("datasource")
local utils = require("utils")

local userdata = {}
local highscores = {}
local data_cache = {}

--- Initialize data container for the given type, read from database if not
--- accessed yet
-- @param type
--
function userdata._init_type(type)
    if data_cache[type] == nil then
        data_cache[type] = datasource.get(type)
        highscores[type] = datasource.get(type .. "_highscores")
        if data_cache[type] == nil then
            data_cache[type] = {}
        end
        if highscores[type] == nil then
            highscores[type] = {}
        end
    end
end

--- Get the user's value for the given type
-- @param type
-- @param user
-- @return The value previously set with set_value or nil if none has been set
function userdata.get_value(type, user)
    userdata._init_type(type)

    return data_cache[type][user]
end

--- Set the user's value for the given type
-- @param type
-- @param user
-- @param value
--
function userdata.set_value(type, user, value)
    userdata._init_type(type)
    data_cache[type][user] = value
    datasource.set(type, data_cache[type])
end

--- Update highscores for type, taking this user's latest total in consideration
-- @param type
-- @param user
-- @param value
--
function userdata.save_highscore(type, user, value)
    userdata._init_type(type)

    local tmp_scores = {}

    local score = {}
    score.user = user
    score.value = value

    tmp_scores[1] = score

    for key, value in pairs(highscores[type]) do
        tmp_scores[key + 1] = value
    end

    local function compare(left, right)
        return left.value > right.value
    end

    table.sort(tmp_scores, compare)

    local unique = utils.unique(
        tmp_scores,
        function (item) return item.user end
    )
    highscores[type] = utils.limit(unique, 3)
    datasource.set(type .. "_highscores", highscores[type])
end

function userdata.get_highscores(type)
    userdata._init_type(type)
    return highscores[type]
end

return userdata
