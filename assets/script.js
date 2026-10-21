(function(){
  // Résumé download
  var resumeButtons = document.querySelectorAll('.resume-download');
  if(resumeButtons.length){
    resumeButtons.forEach(function(btn){
      btn.addEventListener('click', function(){
        handleResumeDownload(btn);
      });
    });
  }
  async function handleResumeDownload(btn){
    var url = btn.getAttribute('data-resume-url');
    var filename = btn.getAttribute('data-resume-filename') || 'Resume.pdf';
    var originalText = btn.textContent;
    btn.disabled = true;
    btn.textContent = 'Preparing…';
    try{
      var downloads = (window.claude && typeof window.claude.use === 'function') ? await window.claude.use('downloads') : null;
      if(downloads){
        var res = await fetch(url);
        var blob = await res.blob();
        await downloads.save({ filename: filename, data: blob });
        btn.textContent = 'Downloaded';
      } else {
        window.open(url, '_blank', 'noopener');
        btn.textContent = originalText;
      }
    }catch(err){
      if(err && err.code === 'declined'){
        btn.textContent = originalText;
      } else {
        window.open(url, '_blank', 'noopener');
        btn.textContent = originalText;
      }
    }finally{
      btn.disabled = false;
      setTimeout(function(){ btn.textContent = originalText; }, 2200);
    }
  }

  // Cite-this citation generator
  var citeModal = document.getElementById('citeModal');
  if(citeModal){
    var citeOutput = document.getElementById('citeOutput');
    var citeTabs = document.getElementById('citeStyleTabs');
    var citeCopyBtn = document.getElementById('citeCopyBtn');
    var citeClose = document.getElementById('citeModalClose');
    var citeBackdrop = document.getElementById('citeModalBackdrop');
    var currentCitations = null;
    var currentStyle = 'apa';
    var lastFocused = null;

    function toAndForm(authors){
      return authors.replace(/\s*&\s*/g, ' and ');
    }
    function bibKey(d){
      var firstWord = (d.title || '').split(/\s+/)[0].toLowerCase().replace(/[^a-z0-9]/g,'');
      return 'tripathy' + (d.year || '') + firstWord;
    }
    function buildCitations(d){
      var out = {};
      if(d.type === 'chapter'){
        out.apa = d.authors + ' (' + d.year + '). ' + d.title + '. In ' + d.editors + ' (Eds.), ' + d.booktitle + (d.pages ? ' (pp. ' + d.pages + ')' : '') + '. ' + d.publisher + '. https://doi.org/' + d.doi;
        out.mla = toAndForm(d.authors) + '. "' + d.title + '." ' + d.booktitle + ', edited by ' + d.editors + ', ' + d.publisher + ', ' + d.year + (d.pages ? ', pp. ' + d.pages : '') + '. doi:' + d.doi + '.';
        out.chicago = toAndForm(d.authors) + '. ' + d.year + '. "' + d.title + '." In ' + d.booktitle + ', edited by ' + d.editors + (d.pages ? ', ' + d.pages : '') + '. ' + d.publisher + '. https://doi.org/' + d.doi + '.';
        out.bibtex = '@incollection{' + bibKey(d) + ',\n  author = {' + toAndForm(d.authors) + '},\n  title = {' + d.title + '},\n  booktitle = {' + d.booktitle + '},\n  editor = {' + d.editors + '},\n' + (d.pages ? '  pages = {' + d.pages + '},\n' : '') + '  year = {' + d.year + '},\n  publisher = {' + d.publisher + '},\n  doi = {' + d.doi + '}\n}';
      } else {
        var volIssue = '';
        if(d.volume){ volIssue += ', ' + d.volume; if(d.issue){ volIssue += '(' + d.issue + ')'; } }
        if(d.pages){ volIssue += ', ' + d.pages; }
        out.apa = d.authors + ' (' + d.year + '). ' + d.title + '. ' + d.journal + volIssue + '. https://doi.org/' + d.doi;
        out.mla = toAndForm(d.authors) + '. "' + d.title + '." ' + d.journal + (d.volume ? ', vol. ' + d.volume : '') + (d.issue ? ', no. ' + d.issue : '') + ', ' + d.year + (d.pages ? ', pp. ' + d.pages : '') + '. doi:' + d.doi + '.';
        out.chicago = toAndForm(d.authors) + '. ' + d.year + '. "' + d.title + '." ' + d.journal + (d.volume ? ' ' + d.volume : '') + (d.issue ? ' (' + d.issue + ')' : '') + (d.pages ? ': ' + d.pages : '') + '. https://doi.org/' + d.doi + '.';
        out.bibtex = '@article{' + bibKey(d) + ',\n  author = {' + toAndForm(d.authors) + '},\n  title = {' + d.title + '},\n  journal = {' + d.journal + '},\n' + (d.volume ? '  volume = {' + d.volume + '},\n' : '') + (d.issue ? '  number = {' + d.issue + '},\n' : '') + (d.pages ? '  pages = {' + d.pages + '},\n' : '') + '  year = {' + d.year + '},\n  doi = {' + d.doi + '}\n}';
      }
      return out;
    }
    function renderCitation(){
      if(!currentCitations) return;
      citeOutput.textContent = currentCitations[currentStyle] || '';
    }
    document.querySelectorAll('.cite-btn').forEach(function(btn){
      btn.addEventListener('click', function(){
        var d = btn.dataset;
        currentCitations = buildCitations(d);
        currentStyle = 'apa';
        citeTabs.querySelectorAll('.cite-style-tab').forEach(function(t){ t.classList.toggle('active', t.dataset.style === 'apa'); });
        renderCitation();
        citeCopyBtn.textContent = 'Copy citation';
        citeCopyBtn.classList.remove('copied');
        lastFocused = btn;
        citeModal.classList.add('open');
        citeModal.setAttribute('aria-hidden', 'false');
        citeClose.focus();
      });
    });
    if(citeTabs){
      citeTabs.querySelectorAll('.cite-style-tab').forEach(function(tab){
        tab.addEventListener('click', function(){
          citeTabs.querySelectorAll('.cite-style-tab').forEach(function(t){ t.classList.remove('active'); });
          tab.classList.add('active');
          currentStyle = tab.dataset.style;
          renderCitation();
          citeCopyBtn.textContent = 'Copy citation';
          citeCopyBtn.classList.remove('copied');
        });
      });
    }
    function closeCiteModal(){
      citeModal.classList.remove('open');
      citeModal.setAttribute('aria-hidden', 'true');
      if(lastFocused){ lastFocused.focus(); }
    }
    if(citeClose){ citeClose.addEventListener('click', closeCiteModal); }
    if(citeBackdrop){ citeBackdrop.addEventListener('click', closeCiteModal); }
    document.addEventListener('keydown', function(e){ if(e.key === 'Escape' && citeModal.classList.contains('open')) closeCiteModal(); });
    if(citeCopyBtn){
      citeCopyBtn.addEventListener('click', function(){
        var text = (currentCitations && currentCitations[currentStyle]) || '';
        function marked(){
          citeCopyBtn.textContent = 'Copied!';
          citeCopyBtn.classList.add('copied');
          setTimeout(function(){ citeCopyBtn.textContent = 'Copy citation'; citeCopyBtn.classList.remove('copied'); }, 1800);
        }
        if(navigator.clipboard && navigator.clipboard.writeText){
          navigator.clipboard.writeText(text).then(marked).catch(function(){
            fallbackCopy(text); marked();
          });
        } else {
          fallbackCopy(text); marked();
        }
      });
    }
    function fallbackCopy(text){
      var ta = document.createElement('textarea');
      ta.value = text;
      ta.style.position = 'fixed';
      ta.style.opacity = '0';
      document.body.appendChild(ta);
      ta.select();
      try{ document.execCommand('copy'); }catch(e){}
      document.body.removeChild(ta);
    }
  }

  // Scroll progress
  var progressBar = document.getElementById('progressBar');
  if(progressBar){
    function updateProgress(){
      var h = document.documentElement;
      var scrolled = (h.scrollTop) / (h.scrollHeight - h.clientHeight) * 100;
      progressBar.style.transform = 'scaleX(' + Math.min(1, Math.max(0, (scrolled || 0) / 100)) + ')';
    }
    document.addEventListener('scroll', updateProgress, { passive:true });
    updateProgress();
  }

  // Mobile nav toggle
  var menuBtn = document.getElementById('menuBtn');
  var mobileNav = document.getElementById('mobileNav');
  if(menuBtn && mobileNav){
    menuBtn.addEventListener('click', function(){
      var open = mobileNav.classList.toggle('open');
      menuBtn.classList.toggle('open', open);
      menuBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
      menuBtn.setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation');
      document.documentElement.style.overflow = open ? 'hidden' : '';
    });
    mobileNav.querySelectorAll('a').forEach(function(a){
      a.addEventListener('click', function(){
        mobileNav.classList.remove('open');
        menuBtn.classList.remove('open');
        menuBtn.setAttribute('aria-expanded','false');
        document.documentElement.style.overflow = '';
      });
    });
  }

  // Curtain-reveal headings
  if('IntersectionObserver' in window){
    var revealObserver = new IntersectionObserver(function(entries){
      entries.forEach(function(entry){
        if(entry.isIntersecting){
          entry.target.classList.add('in-view');
          revealObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.4 });
    document.querySelectorAll('.reveal-heading').forEach(function(el){ revealObserver.observe(el); });
  } else {
    document.querySelectorAll('.reveal-heading').forEach(function(el){ el.classList.add('in-view'); });
  }

  // Design project tag filter (design page only)
  var chips = document.querySelectorAll('.tag-chip');
  var cards = document.querySelectorAll('.project-card');
  if(chips.length && cards.length){
    chips.forEach(function(chip){
      chip.addEventListener('click', function(){
        chips.forEach(function(c){ c.classList.remove('active'); });
        chip.classList.add('active');
        var tag = chip.dataset.tag;
        cards.forEach(function(card){
          var tags = card.dataset.tags.split(' ');
          var show = tag === 'all' || tags.indexOf(tag) > -1;
          card.classList.toggle('hidden', !show);
        });
      });
    });
  }

  // Art & craft lightbox (art page only): reads each work's title, details and image from the page
  var plates = Array.prototype.slice.call(document.querySelectorAll('.art-plate'));
  var lightbox = document.getElementById('lightbox');
  if(plates.length && lightbox){
    var lbTitle = document.getElementById('lightboxTitle');
    var lbMeta = document.getElementById('lightboxMeta');
    var lbThumb = document.getElementById('lightboxThumb');
    var lbEmpty = lbThumb ? lbThumb.innerHTML : '';
    var currentIndex = 0;
    function openLightbox(i){
      currentIndex = i;
      var p = plates[i];
      lbTitle.textContent = p.getAttribute('data-title') || '';
      lbMeta.textContent = p.getAttribute('data-meta') || '';
      if(lbThumb){
        var src = p.getAttribute('data-image');
        if(src){
          lbThumb.innerHTML = '';
          var im = document.createElement('img');
          im.src = src; im.alt = p.getAttribute('data-title') || '';
          lbThumb.appendChild(im);
          lbThumb.classList.add('has-image');
        } else {
          lbThumb.innerHTML = lbEmpty;
          lbThumb.classList.remove('has-image');
        }
      }
      lightbox.classList.add('open');
      lightbox.setAttribute('aria-hidden','false');
      document.getElementById('lightboxClose').focus();
    }
    function closeLightbox(){
      lightbox.classList.remove('open');
      lightbox.setAttribute('aria-hidden','true');
    }
    plates.forEach(function(plate, i){ plate.addEventListener('click', function(){ openLightbox(i); }); });
    document.getElementById('lightboxClose').addEventListener('click', closeLightbox);
    document.getElementById('lightboxBackdrop').addEventListener('click', closeLightbox);
    document.getElementById('lightboxPrev').addEventListener('click', function(){ openLightbox((currentIndex - 1 + plates.length) % plates.length); });
    document.getElementById('lightboxNext').addEventListener('click', function(){ openLightbox((currentIndex + 1) % plates.length); });
    document.addEventListener('keydown', function(e){ if(e.key === 'Escape' && lightbox.classList.contains('open')) closeLightbox(); });
  }
  // Copy email address (inline pill on home + footer button)
  function copyText(text, onDone){
    function legacy(){
      var ta = document.createElement('textarea');
      ta.value = text; ta.setAttribute('readonly',''); ta.style.position = 'fixed'; ta.style.opacity = '0';
      document.body.appendChild(ta); ta.select();
      var ok = false; try{ ok = document.execCommand('copy'); }catch(e){}
      document.body.removeChild(ta); onDone(ok);
    }
    if(navigator.clipboard && navigator.clipboard.writeText){
      navigator.clipboard.writeText(text).then(function(){ onDone(true); }).catch(legacy);
    } else { legacy(); }
  }
  document.querySelectorAll('.copy-email, .copy-email-btn').forEach(function(btn){
    var label = btn.textContent;
    btn.addEventListener('click', function(){
      copyText(btn.getAttribute('data-email'), function(ok){
        btn.textContent = ok ? 'Copied' : 'Select the address to copy';
        btn.classList.remove('done'); void btn.offsetWidth; btn.classList.add('done');
        setTimeout(function(){ btn.textContent = label; }, 1800);
      });
    });
  });



  // Reveal blocks that start below the fold (content above it is never hidden)
  var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if('IntersectionObserver' in window && !reduceMotion){
    var targets = document.querySelectorAll('.about-block > h2, .research-block > h2, .entry-meta, .entry-role, .entry-org, .entry-detail > p, .entry-detail > ul:not(.course-list), .course-list > li, .course-group-label, .project-card, .art-plate, .pub-list > li, .tag-filter, .page-teaching .entry > *, .shot, .project-pager, .project-sections .row, .gallery-heading, .related-list > li');
    var io = new IntersectionObserver(function(entries){
      entries.forEach(function(e){ if(e.isIntersecting){ e.target.classList.add('shown'); io.unobserve(e.target); } });
    }, { rootMargin:'0px 0px -8% 0px', threshold:0.05 });
    var fold = window.innerHeight;
    targets.forEach(function(el, i){
      if(el.getBoundingClientRect().top > fold * 0.92){
        el.classList.add('reveal');
        el.style.transitionDelay = ((i % 4) * 70) + 'ms';
        io.observe(el);
      }
    });
    // safety: never leave anything hidden
    setTimeout(function(){ document.querySelectorAll('.reveal:not(.shown)').forEach(function(el){
      if(el.getBoundingClientRect().top < window.innerHeight) el.classList.add('shown');
    }); }, 1500);
  }

  // Filtered projects fade in
  document.querySelectorAll('.tag-chip').forEach(function(chip){
    chip.addEventListener('click', function(){
      document.querySelectorAll('.project-card').forEach(function(card){
        card.classList.remove('just-shown', 'reveal'); card.classList.add('shown');
        if(!card.classList.contains('hidden')){ void card.offsetWidth; card.classList.add('just-shown'); }
      });
    });
  });
  // ---- Accessibility: language, dialog focus, menu keys ----
  if(!document.documentElement.lang){ document.documentElement.lang = 'en'; }

  var FOCUSABLE = 'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])';
  var dialogs = [document.getElementById('citeModal'), document.getElementById('lightbox')].filter(Boolean);
  var returnTo = null;

  // remember what opened a dialog, so focus can go back there on close
  document.addEventListener('click', function(e){
    var opener = e.target.closest && e.target.closest('.cite-btn, .art-plate');
    if(opener){ returnTo = opener; }
  }, true);

  function openDialog(){ return dialogs.find(function(d){ return d.classList.contains('open'); }); }

  dialogs.forEach(function(d){
    new MutationObserver(function(){
      var isOpen = d.classList.contains('open');
      document.documentElement.style.overflow = isOpen ? 'hidden' : '';
      if(!isOpen && returnTo && document.contains(returnTo)){ returnTo.focus(); returnTo = null; }
    }).observe(d, { attributes:true, attributeFilter:['class'] });
  });

  document.addEventListener('keydown', function(e){
    var d = openDialog();
    if(d && e.key === 'Tab'){
      var items = Array.prototype.filter.call(d.querySelectorAll(FOCUSABLE), function(el){ return el.offsetParent !== null; });
      if(!items.length) return;
      var first = items[0], last = items[items.length - 1];
      if(e.shiftKey && document.activeElement === first){ e.preventDefault(); last.focus(); }
      else if(!e.shiftKey && document.activeElement === last){ e.preventDefault(); first.focus(); }
      else if(!d.contains(document.activeElement)){ e.preventDefault(); first.focus(); }
    }
    if(d && d.id === 'lightbox' && (e.key === 'ArrowLeft' || e.key === 'ArrowRight')){
      var btn = document.getElementById(e.key === 'ArrowLeft' ? 'lightboxPrev' : 'lightboxNext');
      if(btn){ e.preventDefault(); btn.click(); }
    }
    var nav = document.getElementById('mobileNav'), mbtn = document.getElementById('menuBtn');
    if(e.key === 'Escape' && nav && nav.classList.contains('open')){
      nav.classList.remove('open'); mbtn.classList.remove('open'); mbtn.setAttribute('aria-expanded', 'false'); mbtn.setAttribute('aria-label', 'Open navigation'); document.documentElement.style.overflow = ''; mbtn.focus();
    }
  });
})();
(function(){
  // Fallback page transition for browsers without native cross-document view transitions
  if('onpagereveal' in window) return;
  if(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  document.addEventListener('click', function(e){
    if(e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    var a = e.target.closest && e.target.closest('a[href]');
    if(!a || a.target || a.hasAttribute('download')) return;
    var href = a.getAttribute('href');
    if(!href || href.charAt(0) === '#' || /^(mailto:|tel:|https?:)/i.test(href) || !/\.html(\?|#|$)/.test(href)) return;
    e.preventDefault();
    document.body.classList.add('page-leaving');
    setTimeout(function(){ window.location.href = a.href; }, 160);
  });
  window.addEventListener('pageshow', function(){ document.body.classList.remove('page-leaving'); });
})();

