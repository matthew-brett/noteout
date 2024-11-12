--[[
This filter is for debugging JSON output from Quarto.

Enable this filter to dump JSON files with the generated AST
after processing through Quarto.

This can be useful to debug errors in Panflute parsing, for example.
]]

-- Maximum number of JSON files to dump.
MAX_N = 999

return {
    Pandoc = function (doc)
        local json_str = pandoc.json.encode(doc)
        local fn
        local f
        local i = 0
        while i <= MAX_N do
            fn = string.format('doc_%03d.json', i)
            f = io.open(fn, "r")
            if f == nil then break end
            f:close()
            i = i + 1
        end
        if i > MAX_N then error('Ran out of doc_ files') end
        f = assert(io.open(fn, 'w'))
        f:write(json_str)
        f:close()
    end
}
