(() => {
  function getCSRFToken () {
    const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]')
    if (csrfInput) {
      return csrfInput.value
    } else {
      // Get token from cookie:
      // https://docs.djangoproject.com/en/5.0/howto/csrf/#acquiring-the-token-if-csrf-use-sessions-and-csrf-cookie-httponly-are-false
      if (document.cookie && document.cookie !== '') {
        const name = 'csrftoken'
        const cookies = document.cookie.split(';')
        for (let i = 0; i < cookies.length; i++) {
          const cookie = cookies[i].trim()
          // Does this cookie string begin with the name we want?
          if (cookie.substring(0, name.length + 1) === (name + '=')) {
            return decodeURIComponent(cookie.substring(name.length + 1))
          }
        }
      }
    }
    throw new Error('No CSRF Token set.')
  }

  /**
   * Create a POST request that adds or removes an item from the watchlist.
   *
   * The item's data is transferred via the form that is embedded within the
   * button's inner HTML. The data is required when adding an item to the
   * watchlist that does not yet exist in the database.
   *
   * @param {HTMLButtonElement} btn the toggle button
   * @returns a new Request instance
   */
  function createToggleRequest (btn) {
    const form = btn.querySelector('form')
    return new Request(btn.dataset.url, {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCSRFToken()
      },
      body: new FormData(form),
      mode: 'same-origin'
    })
  }

  /**
   * Create a POST request that removes an item from the watchlist.
   *
   * The item to remove is identified by the refnr set in the button's dataset.
   *
   * @param {HTMLButtonElement} btn the remove button
   * @returns a new Request instance
   */
  function createRemoveRequest (btn) {
    const form = new FormData()
    form.append('refnr', btn.dataset.refnr)
    return new Request(btn.dataset.url, {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCSRFToken()
      },
      body: form,
      mode: 'same-origin'
    })
  }

  /**
   * Remove all watchlist items.
   */
  function removeAll () {
    const container = document.querySelector('.watchlist-container')
    if (container) {
      container.innerHTML = '<p>Keine Ergebnisse</p>'
    }
  }

  /**
   * Initialize a watchlist button, adding a click event handler.
   *
   * The event handler will make a request against the URL declared in
   * the button's dataset property. The second argument ``handleResponse``
   * will be called with the clicked button and the response to act on the
   * response.
   *
   * Then, if provided, the third argument ``callback`` will be called with
   * the button and the data returned by ``handleResponse``.
   *
   * @param {HTMLButtonElement} btn the button to initialize
   * @param {CallableFunction} handleResponse a function that handles the response
   * @param {CallableFunction} callback an optional function called at the end of the click event handling
   * @param {CallableFunction} callback an optional function responsible for generating the request
   */
  function initButton (btn, handleResponse, callback, requestFactory) {
    if (btn.initialized) {
      console.log(`${btn} already initialized.`)
      return
    }
    btn.addEventListener('click', (event) => {
      event.preventDefault()
      fetch(requestFactory(btn))
        .then(response => handleResponse(btn, response))
        .then(data => { if (callback) { callback(btn, data) } })
        .catch((error) => console.log(`watchlist button ${btn} error: ${error}`))
    })
    btn.initialized = true
  }

  /**
     * Initialize a 'toggle' button that adds an item to the watchlist, or
     * removes an item from the watchlist if it is already on the watchlist.
     */
  function initToggleButton (btn, callback) {
    const _callback = (btn, data) => {
      // always toggle the 'on-watchlist' class
      if (data) {
        if (data.on_watchlist) {
          btn.classList.remove('text-primary')
          btn.classList.add('text-success')
          btn.classList.add('on-watchlist')
        } else {
          btn.classList.add('text-primary')
          btn.classList.remove('text-success')
          btn.classList.remove('on-watchlist')
        }
      }
      if (callback) callback(btn, data)
    }
    const handleResponse = (btn, response) => {
      if (!response.ok) {
        throw new Error(`Toggle response was not ok (status code: ${response.status})`)
      }
      return response.json()
    }
    initButton(btn, handleResponse, _callback, createToggleRequest)
  }

  /**
     * Initialize a 'remove' button that removes a single item from the
     * watchlist. Used on the watchlist overview.
     */
  function initRemoveButton (btn, callback) {
    const handleResponse = (btn, response) => {
      if (response.ok) {
        if (btn.closest('.watchlist-items-list').children.length === 1) {
          // This is the only watchlist item.
          removeAll()
        } else {
          btn.closest('.watchlist-item').remove()
        }
      }
      return response.json()
    }
    initButton(btn, handleResponse, callback, createRemoveRequest)
  }

  /**
     * Initialize a 'remove all' button that removes all items of a model from
     * the watchlist. Used on the watchlist overview.
     */
  function initRemoveAllButton (btn, callback) {
    const handleResponse = (btn, response) => {
      if (response.ok) removeAll()
      return response.json()
    }
    initButton(btn, handleResponse, callback, createRemoveRequest)
  }

  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.watchlist-toggle-btn').forEach((btn) => initToggleButton(btn))
    document.querySelectorAll('.watchlist-remove-btn').forEach((btn) => initRemoveButton(btn))
    document.querySelectorAll('.watchlist-remove-all-btn').forEach((btn) => initRemoveAllButton(btn))
  })
})()
