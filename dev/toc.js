// Populate the sidebar
//
// This is a script, and not included directly in the page, to control the total size of the book.
// The TOC contains an entry for each page, so if each page includes a copy of the TOC,
// the total size of the page becomes O(n**2).
class MDBookSidebarScrollbox extends HTMLElement {
    constructor() {
        super();
    }
    connectedCallback() {
        this.innerHTML = '<ol class="chapter"><li class="chapter-item expanded "><a href="introduction.html"><strong aria-hidden="true">1.</strong> Introduction</a></li><li class="chapter-item expanded "><a href="getting_started/continuum_mechanics.html"><strong aria-hidden="true">2.</strong> Continuum Mechanics</a></li><li><ol class="section"><li class="chapter-item expanded "><a href="getting_started/rigid_body_motion.html"><strong aria-hidden="true">2.1.</strong> Rigid Body Motion</a></li><li class="chapter-item expanded "><a href="getting_started/simple_shear.html"><strong aria-hidden="true">2.2.</strong> Simple Shear</a></li></ol></li><li class="chapter-item expanded "><a href="getting_started/finite_element_method.html"><strong aria-hidden="true">3.</strong> Finite Element Method</a></li><li class="chapter-item expanded "><a href="getting_started/image_generation.html"><strong aria-hidden="true">4.</strong> Image Generation</a></li><li><ol class="section"><li class="chapter-item expanded "><a href="getting_started/subimage.html"><strong aria-hidden="true">4.1.</strong> Subimage Generation</a></li></ol></li><li class="chapter-item expanded "><a href="getting_started/preprocessing.html"><strong aria-hidden="true">5.</strong> Image Preprocessing</a></li><li><ol class="section"><li class="chapter-item expanded "><a href="getting_started/brightness_contrast.html"><strong aria-hidden="true">5.1.</strong> Brightness and Contrast</a></li><li class="chapter-item expanded "><a href="getting_started/windowing.html"><strong aria-hidden="true">5.2.</strong> Windowing</a></li></ol></li><li class="chapter-item expanded "><a href="getting_started/transformation.html"><strong aria-hidden="true">6.</strong> Image Transformation</a></li><li class="chapter-item expanded "><a href="getting_started/single_point_motion.html"><strong aria-hidden="true">7.</strong> Single Point Motion</a></li><li><ol class="section"><li class="chapter-item expanded "><a href="getting_started/cross_correlation.html"><strong aria-hidden="true">7.1.</strong> Cross Correlation (CC)</a></li><li class="chapter-item expanded "><a href="getting_started/correlation_criteria.html"><strong aria-hidden="true">7.2.</strong> Correlation Criteria</a></li><li class="chapter-item expanded "><a href="getting_started/correlation_visualization.html"><strong aria-hidden="true">7.3.</strong> Correlation Visualization</a></li></ol></li><li class="chapter-item expanded "><a href="getting_started/multi_point_motion.html"><strong aria-hidden="true">8.</strong> Multi-Point Motion</a></li><li><ol class="section"><li class="chapter-item expanded "><a href="getting_started/simple_stretch.html"><strong aria-hidden="true">8.1.</strong> Simple Stretch</a></li><li class="chapter-item expanded "><a href="getting_started/recoverable_displacement_range.html"><strong aria-hidden="true">8.2.</strong> Recoverable Displacement Range</a></li><li class="chapter-item expanded "><a href="getting_started/pure_rotation.html"><strong aria-hidden="true">8.3.</strong> Pure Rotation</a></li><li class="chapter-item expanded "><a href="getting_started/search_center_predictions.html"><strong aria-hidden="true">8.4.</strong> Search Center Predictions</a></li></ol></li><li class="chapter-item expanded "><a href="getting_started/parallelization.html"><strong aria-hidden="true">9.</strong> Parallelization</a></li><li><ol class="section"><li class="chapter-item expanded "><a href="getting_started/subpixel_accuracy.html"><strong aria-hidden="true">9.1.</strong> Subpixel Accuracy</a></li><li class="chapter-item expanded "><a href="getting_started/high_point_density.html"><strong aria-hidden="true">9.2.</strong> High Point Density</a></li><li class="chapter-item expanded "><a href="getting_started/timing_at_scale.html"><strong aria-hidden="true">9.3.</strong> Timing at Scale</a></li></ol></li><li class="chapter-item expanded "><a href="getting_started/path_forward.html"><strong aria-hidden="true">10.</strong> Path Forward</a></li><li class="chapter-item expanded "><a href="contributing.html"><strong aria-hidden="true">11.</strong> Contributing</a></li></ol>';
        // Set the current, active page, and reveal it if it's hidden
        let current_page = document.location.href.toString().split("#")[0].split("?")[0];
        if (current_page.endsWith("/")) {
            current_page += "index.html";
        }
        var links = Array.prototype.slice.call(this.querySelectorAll("a"));
        var l = links.length;
        for (var i = 0; i < l; ++i) {
            var link = links[i];
            var href = link.getAttribute("href");
            if (href && !href.startsWith("#") && !/^(?:[a-z+]+:)?\/\//.test(href)) {
                link.href = path_to_root + href;
            }
            // The "index" page is supposed to alias the first chapter in the book.
            if (link.href === current_page || (i === 0 && path_to_root === "" && current_page.endsWith("/index.html"))) {
                link.classList.add("active");
                var parent = link.parentElement;
                if (parent && parent.classList.contains("chapter-item")) {
                    parent.classList.add("expanded");
                }
                while (parent) {
                    if (parent.tagName === "LI" && parent.previousElementSibling) {
                        if (parent.previousElementSibling.classList.contains("chapter-item")) {
                            parent.previousElementSibling.classList.add("expanded");
                        }
                    }
                    parent = parent.parentElement;
                }
            }
        }
        // Track and set sidebar scroll position
        this.addEventListener('click', function(e) {
            if (e.target.tagName === 'A') {
                sessionStorage.setItem('sidebar-scroll', this.scrollTop);
            }
        }, { passive: true });
        var sidebarScrollTop = sessionStorage.getItem('sidebar-scroll');
        sessionStorage.removeItem('sidebar-scroll');
        if (sidebarScrollTop) {
            // preserve sidebar scroll position when navigating via links within sidebar
            this.scrollTop = sidebarScrollTop;
        } else {
            // scroll sidebar to current active section when navigating via "next/previous chapter" buttons
            var activeSection = document.querySelector('#sidebar .active');
            if (activeSection) {
                activeSection.scrollIntoView({ block: 'center' });
            }
        }
        // Toggle buttons
        var sidebarAnchorToggles = document.querySelectorAll('#sidebar a.toggle');
        function toggleSection(ev) {
            ev.currentTarget.parentElement.classList.toggle('expanded');
        }
        Array.from(sidebarAnchorToggles).forEach(function (el) {
            el.addEventListener('click', toggleSection);
        });
    }
}
window.customElements.define("mdbook-sidebar-scrollbox", MDBookSidebarScrollbox);
