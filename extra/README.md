# Extra files useful with Noteout filters

* `add-meta.lua` — filter that adds metadata from Pandoc and Quarto to JSON
  metadata of document, so JSON filters can use this information.
* `write-json.lua` — filter to output JSON to numbered documents `doc_001.json`
  etc.  You might use this for debugging, when tools like Panflute are breaking
  on the emitted JSON.
