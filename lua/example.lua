
function sum_example(...)
    local sum = 0
    for key, value in ipairs(arg) do
        sum = sum + tonumber(value)
    end

    return sum
end

function increment_example()
    local counter = _G["datasource"]["counter"]
    counter = counter + 1
    _G["datasource"]["counter"] = counter

    return counter
end
