# https://jt-flask-movie-ledger.herokuapp.com/

Site Title: The Movie Ledger

Description: A place to keep to a record of all the movies you've watched, regardless of platform.  Never rack your brain again, trying to remember "What was that movie or series, again?!"


Features
- Profile: create an anonymous profile.  With just a username, password and email address (necessary for password resets).  No sensitive information required.  Edit your profile at anytime!

- Profile export: export your list of movies at anytime!

- Profile delete: delete your profile at any time, all data is wiped from our database.

- Movie/Series Search: using the the OMDB api, browse through thousands of movies or series to find the title you are looking for.

- Store: store the movie or series title in your list for quick browsing.

- Movie/Series Detail: access details of the movie or series you have stored in your list!

- Platform Viewed: optionally, add the platform that viewed the movie/series on.  Especially good if the series/movie was an "original"!

- Favorite:  Add your movie as a favorite movie, so that it will appear at the top of your list!

- Movie Sort: sort your viewed movies by title, year, or date added to your list.



User Flow:
1. User visits the home page.  They can login, or signup.
2. User signs up for our service and is directed to the movie search page.
    - user is greeted with a note
3. User searches for a movie using the title, or actor.
    - this is an ajax search page
    - an api call is made to the OMDB api
    - user can browse through the search results by page
    - each movie/series displayed has an ajax "Add to Ledger"
    - if the movie/series is alread in the list, an "Movie in Ledger" note is displayed
4. User clicks on a result and the details of that movie are displayed on a new page.
    - this will be another API call to get the movie details by ID
5. User can add the movie from this detail page as well, or go back to view the results of the search.
    - this add function will be a form submission
    - if a user adds this movie, they will be redirected to their profile page
    - the go back function should NOT refresh the previous page, but keep the results of the that page
6. User adds a movie from the details page and is redirectd to the "My List" page.
7. "My List" page contains a list of the movies the the user has viewed.  Here, a users favorite movies will be displayed at the top of the page, with the remaining movies displayed below.
    - this page will also be an ajax loaded page.
    - sort results buttons will be ajax buttons that sort the already loaded movies.
8. Movie Sort function (working)
    - this will be an ajax function to reorder the already loaded movies.


Technology Stack:
PostgreSQL
Flask (backend)
Html, css, javascript (front end)