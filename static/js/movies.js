const removeButtons = document.getElementsByTagName("button")
const favButtons = document.getElementsByTagName("i")


for (let el of removeButtons){
  el.addEventListener('click', deleteMovie)
}

function deleteMovie(e){
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


for (let el of favButtons){
  el.addEventListener('click', toggleFavorite)
}

function toggleFavorite(e){
  e.preventDefault();

  const movieID = e.target.getAttribute("data-id")

  /**
   * favorite:
   * far = false
   * fas = true
   */

  axios.post(`/movie/${movieID}/favorite`)
  .then(resp => {
    if (resp.status == 200) {
      console.log("Favorite: ", resp.data.favorite)
      if(resp.data.favorite){
        e.target.className = ("fas fa-star ml__my-movies--movie-fav")
      } else {
        e.target.className = ("far fa-star ml__my-movies--movie-fav")
      }
    }
  })
  .catch((err) => console.log("err: ", err))
}