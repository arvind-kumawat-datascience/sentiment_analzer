from flask import Flask, render_template, redirect, url_for, request 
from flask import Flask, render_template, request 
from imdb import IMDb 
from nltk.sentiment import SentimentIntensityAnalyzer 
from bs4 import BeautifulSoup 
import requests 
 
app = Flask(__name__) 
analyzer = SentimentIntensityAnalyzer() 
 
@app.route('/', methods=['GET', 'POST']) 
def index(): 
    if request.method == 'POST': 
        analysis_type = request.form['analysis'] 
        if analysis_type == 'products': 
            return redirect(url_for('products')) 
        elif analysis_type == 'movies': 
            return redirect(url_for('movies')) 
    return render_template('index.html') 
 
@app.route('/products') 
def products(): 
    return render_template('products/products.html') 
 
@app.route('/movies') 
def movies(): 
    return render_template('movies/movies.html') 
 
@app.route('/search') 
def movies_search(): 
    query = request.args.get('query') 
    ia = IMDb() 
    movies = ia.search_movie(query) 
    results = [] 
    for movie in movies: 
        result = { 
            'title': movie['title'], 
            'link': f"/movie/{movie.movieID}" 
        } 
        results.append(result) 
    return render_template('movies/movies_search_results.html', query=query, 
results=results) 
 
 
@app.route('/movie/<movie_id>') 
def movies_details(movie_id): 
    ia = IMDb() 
    movie = ia.get_movie(movie_id) 
    title = movie['title'] 
    rating = movie['rating'] 
    actors = [actor['name'] for actor in movie['cast'][:5]] 
    plot = movie['plot'][0] 
 
    return render_template('movies/movies_details.html', title=title, rating=rating, actors=actors, plot=plot, movie_id=movie_id) 
 
@app.route('/movies/analyze', methods=['POST']) 
def movies_analyze(): 
    movie_id = request.form.get('movie_id') 
     
    if movie_id is not None: 
        ia = IMDb() 
        movie = ia.get_movie(movie_id) 
        url = f"https://www.imdb.com/title/tt{movie_id}/reviews" 
 
        # Send a GET request to the IMDb movie URL and retrieve the HTML content 
        response = requests.get(url) 
        html_content = response.text 
 
        # Create a BeautifulSoup object to parse the HTML content 
        soup = BeautifulSoup(html_content, 'html.parser') 
 
        # Extract the review containers from the HTML 
        review_containers = soup.find_all("div", class_="lister-item-content") 
 
        results = [] 
        total_score = 0.0 
        for container in review_containers: 
            review_text = container.find("div", class_="text show-more__control").text.strip() 
            scores = analyzer.polarity_scores(review_text) 
            compound_score = scores['compound'] 
 
            if compound_score >= 0.05: 
                sentiment = 'Positive' 
            elif compound_score <= -0.05: 
                sentiment = 'Negative' 
            else: 
                sentiment = 'Neutral' 
 
            result = { 
                'review': review_text, 
                'sentiment': sentiment, 
                'compound_score': compound_score 
            } 
            results.append(result) 
            total_score += compound_score 
 
        average_score = total_score / len(results) if len(results) > 0 else 0.0 
 
        return render_template('movies/movies_analyze.html', results=results, average_score=average_score) 
     
    return render_template('movies/movies_error.html', message='Invalid movie ID') 
 
@app.route('/search', methods=['POST']) 
def products_search(): 
    query = request.form.get('query') 
    url = f"https://www.flipkart.com/search?q={query}" 
    headers = { 
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0;Win64) AppleWebkit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3' 
    } 
    response = requests.get(url, headers=headers) 
    html_content = response.text 
 
    # Create a BeautifulSoup object to parse the HTML content 
    soup = BeautifulSoup(html_content, 'html.parser') 
 
    # Extract the product containers from the HTML 
    product_containers = soup.find_all("div", class_="_2kHMtA") 
 
    results = [] 
    for container in product_containers: 
        title_element = container.find("div", class_="_4rR01T") 
        link_element = container.find("a", class_="_1fQZEK") 
 
        # Perform error handling to check if elements exist 
        if title_element is None or link_element is None: 
            continue 
 
        title = title_element.text.strip() 
        link = link_element.get('href')
        result = { 
            'title': title, 
            'link': link
        } 
        results.append(result) 
 
    return render_template('products/products_search_results.html', query=query, results=results)
 
@app.route('/product/<product_id>') 
def products_details(product_id): 
    # Retrieve the product details based on the product_id 
    # Add your logic here to fetch the title, description, and price based on the product_id 
    url = f'https://amazon.in/dp/{product_id}' 
 
    headers = { 
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0;Win64) AppleWebkit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3' 
    } 
    response = requests.get(url, headers=headers) 
    soup = BeautifulSoup(response.text, 'html.parser')  
 
    name_element = soup.find('span', class_='a-size-large product-title-word-break')
    desc_element = soup.find('div', class_='a-section a-spacing-medium a-spacing-top-small') 
    price_element = soup.find('span', class_='a-price-whole')
    
    if name_element is None or desc_element is None or price_element is None:
        return render_template('products/products_error.html', message='Product details not found')

    # Extract text content from the elements
    name = name_element.get_value(strip=True)
    description = desc_element.get_value(strip=True)
    price = price_element.get_value(strip=True)

    return render_template('products/products_details.html', name=name, description=description, price=price, product_id=product_id)
 
@app.route('/products/analyze', methods=['POST']) 
def products_analyze(): 
    product_id = request.form.get('product_id') 
 
    url = f'https://www.amazon.in/{product_id}/product-reviews/{product_id}/reviewerType=all_reviews' 
    headers = { 
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0;Win64) AppleWebkit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3' 
    } 
    response = requests.get(url, headers=headers) 
    html_content = response.text 
 
    soup = BeautifulSoup(html_content, 'html.parser') 
 
    review_containers = soup.find_all("div", class_="a-row a-spacing-small review-data") 
 
    results = [] 
    total_score = 0.0 
    for container in review_containers: 
        review_text_element = container.find("span", class_="a-size-base review-text review-text-content").text.strip() 
        if review_text_element: 
            review_text = review_text_element 
            scores = analyzer.polarity_scores(review_text) 
            compound_score = scores['compound'] 
 
            if compound_score >= 0.05:
                sentiment = 'Positive' 
            elif compound_score <= -0.05: 
                sentiment = 'Negative' 
            else: 
                sentiment = 'Neutral' 
 
            result = { 
                'review': review_text, 
                'sentiment': sentiment,  
                'compound_score': compound_score 
            } 
            results.append(result) 
            total_score += compound_score 
 
    average_score = total_score / len(results) if len(results) > 0 else 0.0 
 
    return render_template('products/products_analyze.html', results=results, average_score=average_score, url=url, product_id = product_id) 
 
if __name__ == '__main__': 
    app.run(debug=True) 