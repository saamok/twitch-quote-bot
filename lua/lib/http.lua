local http = {}

--- Send a HTTP POST request to the given URL
-- @param url The destination URL
-- @param data nil or http.data() object with POST data added
-- @param headers nil or http.data() object with request headers added
--
function http.post(url, data, headers)
    return _G["Http"].post(url, data, headers)
end

--- Send a HTTP GET request to the given URL
-- @param url The destination URL
-- @param data nil or http.data() object with URL GET parameters added
-- @param headers nil or http.data() object with request headers added
--
function http.get(url, data, headers)
    return _G["Http"].get(url, data, headers)
end

--- Get an object for containing GET/POST data, or headers
-- @return Object with .add("key", "value") -method
function http.data()
    return _G["TupleData"]()
end

--- Encode any string for safe insertion in URL parameters
-- @param str
-- @return URL encoded string
function http.url_encode(str)
  if (str) then
    str = string.gsub (str, "\n", "\r\n")
    str = string.gsub (str, "([^%w %-%_%.%~])",
        function (c) return string.format ("%%%02X", string.byte(c)) end)
    str = string.gsub (str, " ", "+")
  end
  return str
end

return http