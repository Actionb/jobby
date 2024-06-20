document.addEventListener('DOMContentLoaded', () => {
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

  document.querySelectorAll('.delete-btn').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.preventDefault()
      if (!btn.dataset.url || !btn.dataset.pk) return
      const data = new FormData()
      data.append('pk', btn.dataset.pk)
      const request = new Request(btn.dataset.url, {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCSRFToken()
        },
        body: data,
        mode: 'same-origin'
      })
      fetch(request).then((response) => {
        if (!response.ok) {
          console.log(`Something went wrong deleting this item with pk: '${btn.dataset.pk}. Response status code: ${response.status}`)
          return
        }
        if (btn.closest('.trash-items-list').children.length === 1) {
          const container = document.querySelector('.trash-items-container')
          if (container) container.innerHTML = 'Dein Papierkorb ist leer!'
        } else {
          btn.closest('.trash-item').remove()
        }
        // Update the badge counter in the navbar:
        const badge = document.querySelector(".papierkorb-badge")
        if (badge && parseInt(badge.innerHTML)) {
            badge.innerHTML = parseInt(badge.innerHTML) - 1
        }
      })
    })
  })
})
