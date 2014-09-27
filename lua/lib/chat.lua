local utils = require("utils")
local chat = {}

--- Get a list of users in the stream chat
--
function chat.get_users()
    return utils.list_to_lua(_G["Chat"].get_users())
end

--- Send a message to the stream chat
-- @param text
--
function chat.message(text)
    if text ~= "" then
        _G["Chat"].message(text)
    end
end

return chat
