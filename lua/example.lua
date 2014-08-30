
function sum_example(...)
    local sum = 0
    for key, value in ipairs(arg) do
        sum = sum + tonumber(value)
    end

    return sum
end
