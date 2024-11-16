--[[
This filter adds metadata to the document.

This allows us to add useful information visible to Pandoc and
Quarto, but not available in a Python / Panflute filter.

See: https://quarto.org/docs/extensions/lua-api.html
]]

return {{
    Meta = function (meta)
        for _, fmt in ipairs({'html', 'latex',
                              'docx', 'markdown'}) do
            if quarto.doc.is_format(fmt) then
                out_format = fmt
                break
            end
        end
        meta['quarto-doc-params'] = {
            output_directory = quarto.project.output_directory,
            input_file = quarto.doc.input_file,
            output_file = quarto.doc.output_file,
            out_format = out_format
        }
        return meta
    end
}}
