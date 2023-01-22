const removeButtons = document.getElementsByTagName("button")

for (let el of removeButtons) {
  el.addEventListener('click', deleteMovie)
}

function deleteMovie(e) {
  e.preventDefault();
      
  const movieID = e.target.getAttribute("data-id")

  const config = {
    headers: { 'Content-Type': 'application/json' }
  }

  axios.delete(`/movie/${movieID}`, config)
  .then(resp => {
    if (resp.status == 200) {
      e.target.parentElement.remove()
    }
  })
  .catch((err) => console.log("err: ", err))
}