local datasource = require("datasource")

local spin_data = {}

--- Save the current spin results to persistent storage
--
function _save_spin_data()
    datasource.set("spin_data", spin_data)
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

    if spin_data == nil then
        spin_data = {}
        _save_spin_data()
    end
end

--- Spin the wheel of fortune
-- @param user Name of the user spinning the wheel
-- @return A message to be shown on chat
--
function spin(user)
    local previous = _load_spin(user)

    local wait_time = _get_wait_time(previous["last_spin_time"])

    if wait_time > 0 then
        time_text = _G["human_readable_time"](wait_time)
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

_initialize()

return spin
