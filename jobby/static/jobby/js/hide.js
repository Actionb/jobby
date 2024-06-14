(() => {
  const STORAGE_KEY = 'hidden_results'
  const HIDE_BUTTON_SELECTOR = '.hide-btn'
  const RESULT_ITEM_SELECTOR = 'li.result-item'
  const RESULT_DETAILS_SELECTOR = '.result-details'

  function getHiddenResults () {
    return new Set(Array.from(JSON.parse(window.localStorage.getItem(STORAGE_KEY))))
  }

  function store (hiddenResults) {
    // Can't stringify sets, so turn it into an array and then store it.
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(Array.from(hiddenResults)))
  }

  function getResultItem (btn) {
    return btn.closest(RESULT_ITEM_SELECTOR)
  }

  function getResultDetails (resultItem) {
    return resultItem.querySelector(RESULT_DETAILS_SELECTOR)
  }

  function setHidden (btn) {
    btn.classList.add('hidden')
    const resultItem = getResultItem(btn)
    if (resultItem) {
      resultItem.classList.add('opacity-25')
      const details = getResultDetails(resultItem)
      if (details) details.classList.add('d-none')
    }
  }

  function setShown (btn) {
    btn.classList.remove('hidden')
    const resultItem = getResultItem(btn)
    if (resultItem) {
      resultItem.classList.remove('opacity-25')
      const details = getResultDetails(resultItem)
      if (details) details.classList.remove('d-none')
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    const hiddenResults = getHiddenResults()

    // Add click event handlers for the hide buttons:
    document.querySelectorAll(HIDE_BUTTON_SELECTOR).forEach((btn) => {
      btn.addEventListener('click', (e) => {
        e.preventDefault()
        const refnr = btn.dataset.refnr
        if (!refnr) return
        if (hiddenResults.has(refnr)) {
          hiddenResults.delete(refnr)
          setShown(btn)
        } else {
          hiddenResults.add(refnr)
          setHidden(btn)
        }
        store(hiddenResults)
      })
    })

    // Set initial state of results:
    document.querySelectorAll(RESULT_ITEM_SELECTOR).forEach((resultItem) => {
      const hideBtn = resultItem.querySelector(HIDE_BUTTON_SELECTOR)
      if (hideBtn && hideBtn.dataset.refnr) {
        const refnr = hideBtn.dataset.refnr
        if (hiddenResults.has(refnr)) setHidden(hideBtn)
      }
    })
  })
})()
