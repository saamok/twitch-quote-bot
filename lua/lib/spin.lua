--[==[

Wheel of fortune functions for the bot.

To use these, you need to define two custom commands.
Assuming you're using the default command prefix (!) you can do this with:

!def -ul=user -w spin local spin = require('spin'); return spin.spin(user)
!def -ul=user highscores local spin = require('spin'); return spin.highscores()

--]==]

local datasource = require("datasource")
local utils = require("utils")

local spin_data = {}
local highscores = {}
local spin = {}

--- Save the current spin results to persistent storage
--
function _save_spin_data()
    datasource.set("spin_data", spin_data)
end

--- Save the current highscores to persistent storage
--
function _save_highscore_data()
    datasource.set("spin_highscores", highscores)
end

--- Get a new result for a spin
-- @return An integer value between SPIN_MIN and SPIN_MAX in settings
--
function _get_spin()
    local min = _G["settings"]["SPIN_MIN"]
    local max = _G["settings"]["SPIN_MAX"]
    return math.random(min, max)
end

--- Load the previous spin data for this user
-- @param user
-- @return A table with "value" and "last_spin_time" keys
--
function _load_spin(user)
    local data
    if spin_data[user] == nil then
        data = {}
        data["value"] = 0
        data["last_spin_time"] = 0
    else
        data = spin_data[user]
    end

    return data
end

--- Save a new spin result for the user
-- @param user
-- @param value
--
function _save_spin(user, value)
    spin_data[user] = {}
    spin_data[user]["value"] = value
    spin_data[user]["last_spin_time"] = os.time()

    _save_spin_data()
    _save_highscore(user, value)
end

--- Update highscores, taking this user's latest total in consideration
-- @param user
-- @param value
--
function _save_highscore(user, value)
    local tmp_scores = {}

    local score = {}
    score.user = user
    score.value = value

    tmp_scores[1] = score

    for key, value in pairs(highscores) do
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
    highscores = utils.limit(unique, 3)

    _save_highscore_data()
end

--- Check if enough time has elapsed since the last spin
-- @param last_spin_time
--
function _get_wait_time(last_spin_time)
    local elapsed = os.time() - last_spin_time

    return _G["settings"]["SPIN_TIMEOUT"] - elapsed
end

--- Initialize our spin data from the global persistent storage
--
function _initialize()
    spin_data = datasource.get("spin_data")
    highscores = datasource.get("spin_highscores")

    if spin_data == nil then
        spin_data = {}
        _save_spin_data()
    end

    if highscores == nil then
        highscores = {}
        _save_highscore_data()
    end
end

--- Spin the wheel of fortune
-- @param user Name of the user spinning the wheel
-- @return A message to be shown on chat
--
function spin.spin(user)
    local previous = _load_spin(user)

    local wait_time = _get_wait_time(previous["last_spin_time"])

    if wait_time > 0 then
        local time_text = _G["human_readable_time"](wait_time)
        return user .. ", you still need to wait " .. time_text ..
                " before spinning again. You currently have " ..
                previous["value"] .. " point(s)."
    end

    local new_spin = _get_spin()
    local new_total = previous["value"] + new_spin

    _save_spin(user, new_total)

    return user .. ", the wheel of fortune has granted you " .. new_spin ..
            " point(s)! You now have a total of " .. new_total .. " point(s)."
end

--- Show the current spin highscores
-- @return A message to be shown on chat
--
function spin.highscores()
    local scores = {}
    for key, item in pairs(highscores) do
        scores[key] = item.user .. " with " .. item.value .. " point(s)"
    end

    local message = "The current highscores for the wheel of fortune: " ..
            table.concat(scores, ", ")

    return message
end

--- Clear any cached values
--
function spin.clear_cache()
    highscores = {}
end

_initialize()

return spin
