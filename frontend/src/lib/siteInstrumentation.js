const DEFAULT_TITLE = 'EduMetrics | Student Performance Analytics'
const DEFAULT_DESCRIPTION =
  'EduMetrics is an open-source student performance analytics platform for schools, classes, and report generation.'

function upsertMeta(selector, attributes) {
  let el = document.head.querySelector(selector)
  if (!el) {
    el = document.createElement('meta')
    document.head.appendChild(el)
  }
  Object.entries(attributes).forEach(([k, v]) => el.setAttribute(k, v))
}

function setSeo({ title, description, canonicalPath }) {
  const pageTitle = title || DEFAULT_TITLE
  const pageDescription = description || DEFAULT_DESCRIPTION
  const baseUrl = (import.meta.env.VITE_SITE_URL || window.location.origin || '').replace(/\/$/, '')
  const canonicalHref = `${baseUrl}${canonicalPath || window.location.pathname || '/'}`

  document.title = pageTitle
  upsertMeta('meta[name="description"]', { name: 'description', content: pageDescription })
  upsertMeta('meta[property="og:title"]', { property: 'og:title', content: pageTitle })
  upsertMeta('meta[property="og:description"]', { property: 'og:description', content: pageDescription })
  upsertMeta('meta[property="og:url"]', { property: 'og:url', content: canonicalHref })
  upsertMeta('meta[name="twitter:title"]', { name: 'twitter:title', content: pageTitle })
  upsertMeta('meta[name="twitter:description"]', { name: 'twitter:description', content: pageDescription })

  let canonical = document.head.querySelector('link[rel="canonical"]')
  if (!canonical) {
    canonical = document.createElement('link')
    canonical.setAttribute('rel', 'canonical')
    document.head.appendChild(canonical)
  }
  canonical.setAttribute('href', canonicalHref)
}

function routeSeo(pathname) {
  if (pathname === '/') {
    return {
      title: 'EduMetrics | Upload Student Data',
      description: 'Upload and clean student assessment data for school and class performance analytics.',
    }
  }
  if (pathname === '/overview') {
    return {
      title: 'Dashboard Overview | EduMetrics',
      description: 'View school and class performance snapshots, distributions, and key insights.',
    }
  }
  if (pathname === '/at-risk') {
    return {
      title: 'At-Risk Students | EduMetrics',
      description: 'Identify students who need support using transparent, rule-based risk analytics.',
    }
  }
  if (pathname === '/gaps') {
    return {
      title: 'Gap Analysis | EduMetrics',
      description: 'Analyze gender, class, regional, and term performance gaps with actionable insight.',
    }
  }
  if (pathname === '/subjects') {
    return {
      title: 'Subject Analysis | EduMetrics',
      description: 'Compare subject-level performance, pass rates, and trends across terms.',
    }
  }
  if (pathname === '/term-comparison') {
    return {
      title: 'Term Comparison | EduMetrics',
      description: 'Track term-by-term performance trends for school, class, and student cohorts.',
    }
  }
  if (pathname === '/reports') {
    return {
      title: 'Reports | EduMetrics',
      description: 'Generate class and student reports for sharing, printing, and academic follow-up.',
    }
  }
  if (pathname.startsWith('/student/')) {
    return {
      title: 'Student Profile | EduMetrics',
      description: 'Review a detailed student profile with performance trends and subject breakdown.',
    }
  }
  return { title: DEFAULT_TITLE, description: DEFAULT_DESCRIPTION }
}

function initGa() {
  const measurementId = import.meta.env.VITE_GA_MEASUREMENT_ID
  if (!measurementId || window.__edumetricsGaInitialized) return

  const script = document.createElement('script')
  script.async = true
  script.src = `https://www.googletagmanager.com/gtag/js?id=${measurementId}`
  document.head.appendChild(script)

  window.dataLayer = window.dataLayer || []
  window.gtag = window.gtag || function gtag() { window.dataLayer.push(arguments) }
  window.gtag('js', new Date())
  window.gtag('config', measurementId, { send_page_view: false })
  window.__edumetricsGaInitialized = true
}

function trackPageView(pathname) {
  const measurementId = import.meta.env.VITE_GA_MEASUREMENT_ID
  if (!measurementId || typeof window.gtag !== 'function') return
  window.gtag('event', 'page_view', {
    page_path: pathname,
    page_location: `${window.location.origin}${pathname}`,
    page_title: document.title,
  })
}

export function applyRouteInstrumentation(pathname) {
  const seo = routeSeo(pathname)
  setSeo({ ...seo, canonicalPath: pathname })
  initGa()
  trackPageView(pathname)
}
