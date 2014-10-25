--[==[

Wheel of fortune functions for the bot.

To use these, you need to define two custom commands.
Assuming you're using the default command prefix (!) you can do this with:

!def -ul=user -w spin local spin = require('spin'); return spin.spin(user)
!def -ul=user highscores local spin = require('spin'); return spin.highscores()

--]==]

local userdata = require("userdata")

local spin_currency = _G["settings"]["SPIN_CURRENCY"]
local spin = {}

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
    local last_spin = userdata.get_value(spin_currency, user)
    if last_spin == nil then
        data = {}
        data["value"] = 0
        data["last_spin_time"] = 0
    else
        data = {}
        data["value"] = last_spin
        last_spin_time = userdata.get_value(spin_currency ..
                "_last_spin", user)
        if last_spin_time == nil then
            last_spin_time = 0
        end
        data["last_spin_time"] = last_spin_time
    end

    return data
end

--- Save a new spin result for the user
-- @param user
-- @param value
--
function _save_spin(user, value)
    local timestamp = os.time()

    userdata.set_value(spin_currency, user, value)
    userdata.set_value(spin_currency .. "_last_spin", user, timestamp)
    userdata.save_highscore(spin_currency, user, value)
end

--- Check if enough time has elapsed since the last spin
-- @param last_spin_time
--
function _get_wait_time(last_spin_time)
    local elapsed = os.time() - last_spin_time

    return _G["settings"]["SPIN_TIMEOUT"] - elapsed
end


--- Spin the wheel of fortune
-- @param user Name of the user spinning the wheel
-- @return A message to be shown on chat
--
function spin.spin(user)
    local previous = _load_spin(user)

    local wait_time = _get_wait_time(previous["last_spin_time"])

    if wait_time > 0 then
        return
    end

    local new_spin = _get_spin()
    local new_total = previous["value"] + new_spin

    _save_spin(user, new_total)

    return user .. ", the wheel of fortune has granted you " .. new_spin ..
            " " .. spin_currency .. "! You now have a total of " ..
            new_total .." " .. spin_currency
end

function spin.cooldown(user)
    local previous = _load_spin(user)
    local wait_time = _get_wait_time(previous["last_spin_time"])

    if wait_time > 0 then
        local time_text = _G["human_readable_time"](wait_time)
        return user .. ", you still need to wait " .. time_text ..
            " before spinning again. You currently have " ..
            previous["value"] .. " " .. spin_currency .. "."
    else
        return user .. ", you can spin right now!"
    end
end

--- Show the current spin highscores
-- @return A message to be shown on chat
--
function spin.highscores()
    local scores = {}
    local highscores = userdata.get_highscores(spin_currency)
    for key, item in pairs(highscores) do
        scores[key] = item.user .. " with " .. item.value .. " " .. spin_currency
    end

    local message = "The current highscores for the wheel of fortune: " ..
            table.concat(scores, ", ")

    return message
end


return spin
