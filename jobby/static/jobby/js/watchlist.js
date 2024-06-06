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
  
    function getRequest (btn) {
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
  
    document.addEventListener('DOMContentLoaded', () => {
      // Add handler for the toggle button:
      document.querySelectorAll('.watchlist-toggle-btn').forEach((btn) => {
        btn.addEventListener('click', (e) => {
          e.preventDefault()
          fetch(getRequest(btn))
            .then(response => {
              if (!response.ok) {
                throw new Error(`Toggle response was not ok (status code: ${response.status})`)
              }
              return response.json()
            })
            .then(data => {
              if (data.on_watchlist) {
                btn.classList.remove('text-primary')
                btn.classList.add('text-success')
                btn.classList.add('on-watchlist')
              } else {
                btn.classList.add('text-primary')
                btn.classList.remove('text-success')
                btn.classList.remove('on-watchlist')
              }
              const link = btn.closest(".result-header").querySelector("a.result-link")
              if (link && data.link_url) link.href = data.link_url
            })
            .catch((error) => console.log(`Error when toggling watchlist: ${error}`))
        })
      })
    })
  })()
  