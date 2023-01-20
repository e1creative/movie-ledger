const myMovies = document.getElementById("myMovieList")

myMovies.addEventListener('click', function(e){
    e.preventDefault();
    if (e.target.tagName == "BUTTON") {
        let formEls = e.target.parentNode.children

        const params = {};
        const config = {
          headers: { 'Content-Type': 'application/json' }
        }
    
        for (let el of formEls) {
          if (el.tagName === "INPUT" && el.type === "hidden") {
            params[el.name] = el.value;
          }
        }
      
        axios.post("/movie/new", JSON.stringify(params), config)
        .then(resp => {
          console.log(resp);
        })
        .catch((err) => console.log(err))
    }
})