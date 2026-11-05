-- {{< paper url="https://doi.org/…" who="Name et al." year="2021" title="…" >}}
--   -> one link: [paper icon] Name et al. (2021), the title on hover.
-- corner="true": the icon alone, at the top right of the slide (a result slide's source).
local function kw(kwargs, k)
  local v = kwargs[k]
  return v and pandoc.utils.stringify(v) or ""
end

return {
  ["paper"] = function(args, kwargs)
    quarto.doc.add_html_dependency({ name = "paper", version = "1.0.0", stylesheets = { "paper.css" } })
    local url, who, year, title = kw(kwargs, "url"), kw(kwargs, "who"), kw(kwargs, "year"), kw(kwargs, "title")
    local corner = kw(kwargs, "corner") == "true"
    local label = who .. (year ~= "" and (" (" .. year .. ")") or "")
    local tip = title ~= "" and (label .. ": " .. title) or label
    local content = { pandoc.Span({}, { class = "paper-icon" }) }
    if not corner then
      content[#content + 1] = pandoc.Space()
      content[#content + 1] = pandoc.Str(label)
    end
    return pandoc.Link(content, url, tip,
      pandoc.Attr("", { "paper-ref", corner and "paper-corner" or nil }, { ["aria-label"] = tip }))
  end,
}
