document.addEventListener('DOMContentLoaded', () => {
  const container = document.querySelector('#textBeschreibung')
  fetch(container.dataset.url).then(response => {
    if (response.ok) {
      return response.text()
    } else {
      throw new Error('Response was not ok.')
    }
  }).then(response_text => {
    const parser = new DOMParser()
    html = parser.parseFromString(response_text, 'text/html')
    container.innerHTML = html.querySelector('body').innerHTML
  }).catch(e => console.log(`fetch failed: ${e}`))
})
