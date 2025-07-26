/*
 * Assign 'docutils' class to tables so styling and
 * JavaScript behavior is applied.
 *
 * https://github.com/mkdocs/mkdocs/issues/2028
 */

$('div.rst-content table').addClass('docutils');
document.addEventListener('DOMContentLoaded', function() {
    // Wait for MkDocs to fully render the page including ToC
    setTimeout(function() {
        Prism.languages.insertBefore('bash', 'comment', {
            'backtick-content': {
                pattern: /`[^`\n]*`/,
                inside: {
                    'punctuation': /`/
                }
            },
            'cmk-recursion': {pattern: /(?:\b)(?:if|and|KG|AG|Agent|Formulae|end|Vars|Actions|Obsvars|Protocol|Evolution|InitStates|Environment)/,}, 
            'cmk-syntax': {pattern: /\b(|jq)\b/,},
            'shell-command': {
                pattern: /(?:echo|cat|apk|wget|tar|apt-get|pip3|pip|npm|ansible) /,
                // alias:'important'
                },
            'shell-install': {
                pattern: /(?:apk|apt-get) /,
                // alias:''
            },
            'cmk-fxn': {
                pattern: /(?:io|log|cmk|docker|Dockerfile|flux|stage|mk|stream|tux)[.]([a-z._])+(?:(\/|,|\())/,},
            'cmk-integral-open':{
                pattern: /^⨖(?!\s+with\b).*$/m,
                inside: {
                    'symbol': /^⨖/,
                    'defname': /\b.*\b/,
                }, alias:'token cmk-line-feed si punctuation cmk-syntax'},
            });
    }, 100); // Small delay to ensure ToC is already processed
    })


function prefixHeader(headerId, txt, style="") {
    heading = findHeader(headerId)
    if (heading) {
        // Create and configure the image element
    zonk = document.createElement('span');
    zonk.appendChild(document.createTextNode(txt));
    const span = Object.assign(
        zonk, 
        // {src: imgSrc}, 
        {style: 'height:2em;margin-right:5px; vertical-align: middle;'+style});
    // Insert the image before the first child of the heading
    heading.insertBefore(span, heading.firstChild);}
}

function findHeader(headerId) {
    // Convert spaces to dashes in header-id
    const processedHeaderId = headerId.toLowerCase().replace(/\s+/g, '-').replace('?','-');
    const headers = document.querySelectorAll('h1, h2, h3, h4, h5, h6, h7');
    // First try exact match (case-insensitive)
    heading = Array.from(headers).find(h => 
        h.id && h.id.toLowerCase() === processedHeaderId.toLowerCase()
    );
    if (!heading) { // If no exact match, try startsWith (case-insensitive)
        heading = Array.from(headers).find(h => 
        h.id && h.id.toLowerCase().startsWith(processedHeaderId.toLowerCase())
        );
    }
    if (!heading) {  // If startsWith fails, try contains substring (case-insensitive)
        heading = Array.from(headers).find(h => 
        h.id && h.id.toLowerCase().includes(processedHeaderId.toLowerCase())
        );
    }
    if (!heading) { // Check if heading was found
        console.error(`No header element found matching '${processedHeaderId}'`);
        return null;
    }
    return heading;
}

function addImageToHeader(headerId, imgSrc,style="") {
    if (!imgSrc.endsWith('.svg')) { imgSrc += '.svg'; }
    heading = findHeader(headerId)
    if (heading) {
        // Create and configure the image element
    const img = Object.assign(document.createElement('img'), 
        {src: imgSrc}, {style: 'height:1.2em;margin-right:5px; vertical-align: middle;'+style});
    // Insert the image before the first child of the heading
    heading.insertBefore(img, heading.firstChild);
    }}

/**
 * Find contiguous blocks of spans with class "inside_define" and wrap them in divs
 * Plain text nodes between spans with the class should be included in the blocks
 * Newlines and <br> tags don't break continuity
 */
function wrapContiguousDefineBlocks() {
    // Get the container element to process
    const container = document.body;
    // Store nodes and tracking variables for each block
    let currentNodes = [];
    let hasDefineSpan = false;
    // Use a TreeWalker to navigate through all nodes
    const walker = document.createTreeWalker(
      container,
      NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT,
      null,
      false
    );
    
    let currentNode = walker.nextNode();
    
    while (currentNode) {
      const nextNode = walker.nextNode(); // Get next node before modifications
      
      if (currentNode.nodeType === Node.ELEMENT_NODE &&
          currentNode.tagName === 'SPAN' &&
          currentNode.classList.contains('inside_define')) {
        // Found a defining span
        currentNodes.push(currentNode);
        hasDefineSpan = true;
      }
      else if (currentNode.nodeType === Node.TEXT_NODE ||
              (currentNode.nodeType === Node.ELEMENT_NODE && currentNode.tagName === 'BR')) {
        // Text nodes and <br> tags - add to current collection
        if (currentNodes.length > 0 || nextNode) {
          currentNodes.push(currentNode);
        }
      }
      else if (currentNode.nodeType === Node.ELEMENT_NODE) {
        // Other element - this breaks the block
        if (hasDefineSpan && currentNodes.length > 0) {
          // We have a complete block - wrap it
          wrapNodesInDefineBlock(currentNodes);
        }
        
        // Reset for next block
        currentNodes = [];
        hasDefineSpan = false;
      }
      
      currentNode = nextNode;
    }
    
    // Handle any remaining block at the end
    if (hasDefineSpan && currentNodes.length > 0) {
      wrapNodesInDefineBlock(currentNodes.slice(1));
    }
  }
  
  /**
   * Wrap a set of nodes in a div with class "define_block"
   * @param {Array} nodes - Array of nodes to wrap
   */
  function wrapNodesInDefineBlock(nodes) {
    if (nodes.length === 0) return;
    
    // Create a new div with class "define_block"
    const defineBlockDiv = document.createElement('span');
    defineBlockDiv.className = 'define_block';
    
    // Insert the div before the first node
    const firstNode = nodes[0];
    firstNode.parentNode.insertBefore(defineBlockDiv, firstNode);
    
    // Move all nodes into the div
    nodes.forEach(node => {
      defineBlockDiv.appendChild(node);
    });
  }
  
//   // Run the function when the DOM is fully loaded
//   document.addEventListener('DOMContentLoaded',);
  
//   // Or run immediately if the DOM is already loaded
//   if (document.readyState === 'complete' || document.readyState === 'interactive') {
//     wrapContiguousDefineBlocks();
//   }