
const movieSearchForm = document.getElementById("movieSearchForm")
const csrfToken = document.getElementById("csrf_token")
const searchTerm = document.getElementById("search_term")
const submitButton = document.getElementById("submitButton")

const searchResults = document.getElementById("searchResults")

searchResults.addEventListener('click', function(e) {
  if (e.target.type === "submit") {
    e.preventDefault();
    
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

movieSearchForm.addEventListener('submit', function(e) {
  e.preventDefault();

  searchResults.innerHTML = "";

  const params = new URLSearchParams();
  params.append('csrf_token', csrfToken.value);
  params.append('search_term', searchTerm.value);
  
  const config = {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  }

  axios.post("/movie/search", params, config)
  .then(function(resp){
    data = resp.data;

    let newH2 = document.createElement("h2")
    newH2.innerText = `Search results for "${searchTerm.value}"`
    searchResults.appendChild(newH2)

    let newUL = document.createElement("ul");
    newUL.classList.add("ml__search-results")       

    data.forEach(element => {
      let newLI = document.createElement("li");
      newLI.classList.add("ml__search-result");

      let newA = document.createElement("a");
      newA.setAttribute("href", `/movie/detail/${element['imdbID']}`)
      
      let newIMG = document.createElement("img") 
      newIMG.classList.add("ml__search-result--image");
      if (element["Poster"] === "N/A" ) {
        newIMG.setAttribute("src", "");
      } else {
        newIMG.setAttribute("src", element["Poster"]);
      }
      newA.appendChild(newIMG)

      let newH3 = document.createElement("h3");
      newH3.classList.add("ml__search-result--title");
      newH3.innerText = element["Title"];
      newA.appendChild(newH3)

      let newP = document.createElement("p");
      newP.classList.add("ml__search-result--year");
      newP.innerText = element["Year"];
      newA.appendChild(newP);
      
      newLI.appendChild(newA);

      let newForm = document.createElement("form");
      newForm.setAttribute("method", "POST");
      newForm.setAttribute("action", "/movie/new");

      /** 
       * create 4 inputs and append to our new form
       * 
       * <input type="hidden" name="imdb_id" value="{{ movie['imdbID'] }}">
       * <input type="hidden" name="title" value="{{ movie['Title'] }}">
       * <input type="hidden" name="year" value="{{ movie['Year'] }}">
       *  <input type="hidden" name="imdb_img" value="{{ movie['Poster'] }}">
       */
      let formChildren = ["imdbID", "Title", "Year", "Poster"]
      
      for (let child of formChildren) {
        let newEl = document.createElement("input");
        newEl.setAttribute("type", "hidden");
        // for imdb_id
        if (child === "imdbID") {
          newEl.setAttribute("name", "imdb_id");
        } else if (child === "Poster"){
          newEl.setAttribute("name", "imdb_img");
        } else {
          newEl.setAttribute("name", child.toLowerCase());
        }
        newEl.setAttribute("value", element[child]);

        newForm.appendChild(newEl)
      }

      // create submit button and append to form
      let newButton = document.createElement("button");
      newButton.setAttribute("type", "submit");
      newButton.innerText = "Add to My List";
      newForm.appendChild(newButton);

      // append our completed form to our li
      newLI.appendChild(newForm)

      // append our completed li to the ul
      newUL.appendChild(newLI)
    });

    // append our UL to the searchResults div
    searchResults.appendChild(newUL)

    searchTerm.value = ""

  })
  .catch(function(err){
      console.log(err)
  })
})