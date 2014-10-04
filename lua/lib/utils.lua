local utils = {}

--- Convert a given list of items to a "set" so you can check items' existence
--- easily. s = utils.Set({"a", "b"}); if s["a"] then ... end
-- @param list
--
function utils.Set(list)
    local set = {}
    for _, l in ipairs(list) do
        set[l] = true
    end
    return set
end

--- Cleans the "n" item off your "arg" object
-- @param args The arg object on a function taking ... arguments
-- @return A table with the "n" item cleaned off
--
function utils.clean_arg(args)

    local options = {}
    for k, v in pairs(args) do
        if k ~= "n" then
            options[k] = v
        end
    end

    return options
end

--- Return a random item of the given arguments
-- @param ... Any number of options
-- @return One of the given options
function utils.random(...)
    local options = utils.clean_arg(arg)
    local index = math.random(1, #options)

    return options[index]
end

--- Filter the list to only include unique entries
-- @param values List of values
-- @param func Function to return the item's unique key
-- @return List of unique values, with sequential keys
function utils.unique(values, func)
    -- List of unique keys we have encountered so far
    local unique_keys = {}

    local unique_key
    local key_adjustment = 0

    local result = {}
    for key, value in pairs(values) do
        unique_key = func(value)

        if unique_keys[unique_key] == nil then
            unique_keys[unique_key] = true
            result[key + key_adjustment] = value
        else
            key_adjustment = key_adjustment - 1
        end
    end

    return result
end

--- Limit the length of the given table to the given length
-- @param values List of values
-- @param length Maximum length
-- @return List of values up to the maximum length
function utils.limit(values, length)
    local result = {}
    local result_length = 0

    for key, value in pairs(values) do
        if result_length < length then
            result[key] = value
            result_length = result_length + 1
        end
    end

    return result
end

--- Call the given function in the given number of seconds (roughly)
-- @param seconds Number of seconds
-- @param callback Function to be called
-- @return The stop() function
function utils.delayed(seconds, callback)
    local reference = _G["Delayed"](seconds, callback)

    local stop = function()
        reference.cancel()
    end

    return stop
end

--- Call the given function every X seconds (roughly)
-- @param seconds Number of seconds
-- @param callback Function to be called
-- @return The stop() function
function utils.interval(seconds, callback)
    local reference = _G["Interval"](seconds, callback)

    local stop = function()
        reference.cancel()
    end

    return stop
end

--- Convert a Python list to a Lua table
-- @param list
-- @return The Lua table
function utils.list_to_lua(list)
    local result = {}
    local i = 1

    for item in python.iter(list) do
        result[i] = item
        i = i + 1
    end

    return result
end

return utils
