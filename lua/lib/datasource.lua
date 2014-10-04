--[==[

Global datasource access functions

Provide a consistent method of communicating data between Lua and the Python
persistent data store.

--]==]

local json = require("dkjson")

local datasource = {}

--- Get a value from the persistent data source
-- @param key Name of the value to get
-- @return The stored data
function datasource.get(key)
    local json_data = _G["datasource"].get(key)
    local value, position, error = json.decode(json_data)
    return value
end


--- Set a value to the persistent data source
-- @param key Name of the value
-- @param value Stored data
function datasource.set(key, value)
    local json_data = json.encode(value)
    _G["datasource"].set(key, json_data)
end

return datasource
