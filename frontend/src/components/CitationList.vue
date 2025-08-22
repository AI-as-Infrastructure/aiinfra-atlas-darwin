<template>
	<div v-if="displayedCitations.length">
	  <h5 class="title is-6">Citations</h5>
			<ul>
				<li v-for="(c, idx) in displayedCitations" :key="idx" style="margin-bottom: 0.5em;">
					<span
						class="has-tooltip-arrow"
						:title="c.tooltip || c.quote"
					>
						<a v-if="c.url" :href="c.url" target="_blank">[{{ idx + 1 }}]</a>
						<span v-else>[{{ idx + 1 }}]</span>
					</span>
							<span style="margin-left: 0.5em;">{{ c.text || c.quote }}</span>
							<span v-if="c.loc" style="margin-left: 0.5em; color:#7a7a7a; font-size: 0.85em;">({{ c.loc }})</span>
							<!-- Inline entity badges (first 2 per type) -->
							<span v-if="c.entities" style="margin-left: 0.5em;">
								<span v-if="c.entities.persons && c.entities.persons.length" class="tag is-light" style="margin-right:0.25em;">
									👤 {{ c.entities.persons.slice(0,2).join(', ') }}<span v-if="c.entities.persons.length>2">…</span>
								</span>
								<span v-if="c.entities.places && c.entities.places.length" class="tag is-light" style="margin-right:0.25em;">
									📍 {{ c.entities.places.slice(0,2).join(', ') }}<span v-if="c.entities.places.length>2">…</span>
								</span>
								<span v-if="c.entities.taxa && c.entities.taxa.length" class="tag is-light" style="margin-right:0.25em;">
									🧬 {{ c.entities.taxa.slice(0,2).join(', ') }}<span v-if="c.entities.taxa.length>2">…</span>
								</span>
							</span>
					<!-- Inline compact bibliography preview (optional) -->
					<span v-if="c.bibliography && (c.bibliographyPreview && c.bibliographyPreview.length)"
								style="margin-left: 0.5em; color: #667; font-size: 0.9em;">
						— {{ c.bibliographyPreview.join('; ') }}
					</span>
				</li>
			</ul>
	  <div v-if="displayedCitations.length > 3">
		<a @click="showAll = true" style="cursor:pointer;">
		  See all {{ displayedCitations.length }} citations
		</a>
	  </div>
	  <div v-if="showAll" class="modal is-active">
		<div class="modal-background" @click="showAll = false"></div>
		<div class="modal-content">
		  <div class="box">
			<h5 class="title is-6">All Citations</h5>
						<ul>
							<li v-for="(c, idx) in displayedCitations" :key="idx" style="margin-bottom: 1em;">
								<div style="margin-bottom: 0.25em;">
									<a v-if="c.url" :href="c.url" target="_blank">[{{ idx + 1 }}] {{ c.text || c.quote }}</a>
									<span v-else>[{{ idx + 1 }}] {{ c.text || c.quote }}</span>
									<div v-if="c.meta || c.source_id"><small>{{ c.meta || c.source_id }}</small></div>
									<div v-if="c.url || c.recommended_citation" style="margin-top:0.25em;">
										<div v-if="c.url"><small><a :href="c.url" target="_blank">{{ c.url }}</a></small></div>
										<div v-if="c.recommended_citation"><small>{{ c.recommended_citation }}</small></div>
									</div>
									<div v-if="c.loc || (c.entities && (c.entities.persons?.length || c.entities.places?.length || c.entities.taxa?.length))" style="margin-top: 0.25em; color:#7a7a7a;">
										<span v-if="c.loc">{{ c.loc }}</span>
										<span v-if="c.entities && c.entities.persons && c.entities.persons.length" style="margin-left:0.5em;">👤 {{ c.entities.persons.join(', ') }}</span>
										<span v-if="c.entities && c.entities.places && c.entities.places.length" style="margin-left:0.5em;">📍 {{ c.entities.places.join(', ') }}</span>
										<span v-if="c.entities && c.entities.taxa && c.entities.taxa.length" style="margin-left:0.5em;">🧬 {{ c.entities.taxa.join(', ') }}</span>
									</div>
								</div>
								<div v-if="c.full_content" style="white-space: pre-wrap; font-size: 0.95em; margin-bottom: 0.5em;">
									{{ c.full_content }}
								</div>
								<!-- Full bibliography rendering -->
								<div v-if="c.bibliography" style="font-size: 0.95em; color: #333;">
									<div v-if="c.bibliography.bibl && c.bibliography.bibl.length">
										<div style="font-weight: 600; margin-bottom: 0.25em;">Bibliography</div>
										<ul style="list-style: disc; margin-left: 1.25em;">
											<li v-for="(b, bi) in c.bibliography.bibl" :key="'bibl-'+bi">{{ b }}</li>
										</ul>
									</div>
									<div v-if="c.bibliography.bibl_struct && c.bibliography.bibl_struct.length" style="margin-top: 0.5em;">
										<div style="font-weight: 600; margin-bottom: 0.25em;">References</div>
										<ul style="list-style: disc; margin-left: 1.25em;">
											<li v-for="(bs, si) in c.bibliography.bibl_struct" :key="'biblStruct-'+si">
												<span v-if="bs.title"><strong>{{ bs.title }}</strong></span>
												<span v-if="bs.authors && bs.authors.length"> — {{ bs.authors.join(', ') }}</span>
												<span v-if="bs.date"> ({{ bs.date }})</span>
												<span v-if="bs.publisher || bs.pub_place"> — {{ [bs.publisher, bs.pub_place].filter(Boolean).join(', ') }}</span>
												<span v-if="bs.ids && bs.ids.length"> — {{ bs.ids.join(', ') }}</span>
												<span v-if="!bs.title && !bs.authors && !bs.date && !bs.publisher && !bs.pub_place && !bs.ids && bs.text">{{ bs.text }}</span>
											</li>
										</ul>
									</div>
								</div>
								<hr>
							</li>
						</ul>
			<button class="button" @click="showAll = false">Close</button>
		  </div>
		</div>
	  </div>
	</div>
  </template>
  
  <script setup>
  import { ref, computed } from 'vue'
  const props = defineProps({
	answer: { type: String, required: false },
	citations: { type: Array, required: false, default: () => [] }
  })
  const showAll = ref(false)
  
  // If we have structured citations, use those directly
  // Otherwise, parse citations from text
  const displayedCitations = computed(() => {
	// If structured citations are provided, use them
	if (props.citations && props.citations.length > 0) {
	  return props.citations.map((citation, index) => {
		const bib = citation.bibliography || null;
		let bibliographyPreview = [];
		if (bib) {
		  if (Array.isArray(bib.bibl) && bib.bibl.length) {
			bibliographyPreview = bibliographyPreview.concat(bib.bibl.slice(0, 1));
		  }
		  if (Array.isArray(bib.bibl_struct) && bib.bibl_struct.length) {
			// Build a compact label like: Title — Author, Year
			const bs = bib.bibl_struct[0];
			const parts = [];
			if (bs.title) parts.push(bs.title);
			const authorLabel = Array.isArray(bs.authors) && bs.authors.length ? bs.authors.join(', ') : null;
			if (authorLabel) parts.push(authorLabel);
			if (bs.date) parts.push(bs.date);
			if (parts.length) bibliographyPreview.push(parts.join(' — '));
		  }
		}
		return {
		number: index + 1,
		text: citation.quote || citation.text,
		url: citation.url,
		meta: citation.source_id || citation.meta,
		tooltip: citation.quote || citation.text,
		full_content: citation.full_content,
		bibliography: bib,
		bibliographyPreview
	  }));
	}
	
	// Otherwise, fall back to parsing from text
	if (!props.answer) return [];
	
	// Split answer into main answer and citation lines
	const citationRegex = /^\[(\d+)\]\s*(.*)$/;
	const lines = props.answer.split('\n');
	
	return lines
	  .map(line => {
		const match = line.match(citationRegex);
		if (match) {
		  // Try to extract metadata (URL, etc.) from the text if present
		  const number = match[1];
		  const text = match[2];
		  // Simple URL extraction (optional, can be improved)
		  const urlMatch = text.match(/https?:\/\/\S+/);
		  const url = urlMatch ? urlMatch[0] : null;
		  // Tooltip/meta extraction (optional, can be improved)
		  const meta = text.replace(url || '', '').trim();
		  return {
			number,
			text,
			url,
			meta,
			tooltip: meta,
			full_content: null // Could be filled if you parse more
		  };
		}
		return null;
	  })
	  .filter(Boolean);
  });
  </script>