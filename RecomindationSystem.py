import pandas as pd
import plotly.express as px

data = pd.read_json('all_books.json')
data = data[data['book_title'].map(lambda x: x.isascii())]
data = data.drop_duplicates(subset=["book_title"])
data = data.drop(['desc', 'book_id', 'num_reviews', 'img'], 1)

mean_average_rating = data['average_rating'].mean()
min_votes = data['num_ratings'].quantile(0.80)
q_books = data.copy().loc[data['num_ratings'] >= min_votes]

# Makes a whighted score based on the number of voters and the average rating
def weighted_rating(metadata, m=min_votes, C=mean_average_rating):
    v = metadata['num_ratings']
    R = metadata['average_rating']
    return (v/(v+m) * R) + (m/(m+v) * C)

def get_list(x):
    if isinstance(x, list):
        elements = [i for i in x]
        #Check if more than 3 elements exist. If yes, return only first three. If no, return entire list.
        if len(elements) > 3:
            elements = elements[:3]
        return elements

    #Return empty list in case of missing data
    return []

def clean_data(x):
    if isinstance(x, list):
        #make the strings as list
        return [str.lower(i.replace(" ", "")) for i in x]
    else:
        #Check if author exists. If not, return empty string
        if isinstance(x, str):
            return str.lower(x.replace(" ", ""))
        else:
            return ''

#read the data according to the given titles
def read_data(titles):
    features = ['author', 'genres']
    chosen_books = pd.DataFrame()
    for title in titles:
        chosen_books = chosen_books.append(data[data['book_title'] == title])
    chosen_books = chosen_books.drop_duplicates(subset=["book_title"])
    for feature in features:
        chosen_books[feature] = chosen_books[feature].apply(clean_data)
    return chosen_books

#returns 2 dictionaries that include the number of occurance of every genre and the author.
def make_dicts(chosen_books):
    sim_dict = {}
    authors_dict = {}
    for i in range(len(chosen_books)): 
        for genre in chosen_books.loc[i, "genres"]:
            if genre not in sim_dict:
                sim_dict[genre] = 1
            else:
                sim_dict[genre] += 1
        if chosen_books.loc[i, "author"] not in authors_dict:
            authors_dict[chosen_books.loc[i, "author"]] = 1
        else:
            authors_dict[chosen_books.loc[i, "author"]] += 1
    return sim_dict, authors_dict

# adds a score to every book based on the dictionaries mintioned in the above function
def add_scores(q_books, sim_dict, authors_dict):
    for i in range(len(q_books)):
        for j in q_books.loc[i, "genres"]:
            if j in sim_dict:
                q_books.loc[i, "sim_score"] += sim_dict[j]
        if q_books.loc[i ,"author"] in authors_dict:
            q_books.loc[i, "sim_score"] += authors_dict[q_books.loc[i ,"author"]]

# returnes the top 20 books that have the highest scores
def recomend_books(q_books, titles):
    chosen_books = pd.DataFrame()
    chosen_books = read_data(titles)
    chosen_books = chosen_books.reset_index(drop=True)
    genres_dict, authors_dict = make_dicts(chosen_books)
    q_books["sim_score"] = 0 
    add_scores(q_books, genres_dict, authors_dict)       
    
    #Sort the values based on the sim_score and reating score
    q_books = q_books.sort_values(by = ['sim_score', 'score'], ascending=False) 
    q_books = q_books.reset_index(drop=True)
    r_dict = {}
    r_list = []
    for i in range(len(q_books)):
        for genre in q_books.loc[i, "genres"]:    
                if genre not in r_dict:
                    r_dict[genre] = 1
        #if the genre is occured more than 7 times stop any recomindation contains it            
        if all(r_dict[genre_] < 7 for genre_ in q_books.loc[i, "genres"]):
            for genre in q_books.loc[i, "genres"]:    
                r_dict[genre] += 1
                r_list.append(q_books.iloc[i])
    r_books = pd.DataFrame(r_list, columns=q_books.columns)   
    # delete duplications in the data
    r_books = r_books.drop_duplicates(subset=["book_title"])
    r_books = r_books[-r_books['book_title'].isin(titles)].head(20)
    r_books = r_books.reset_index(drop=True)
    return r_books

# this function can be used to show the chart of the genres occurance
def show_chart(books):
    dict1 , dict2 = make_dicts(books)        
    dict1 = {'Genres': dict1.keys(), 'Count': dict1.values()}
    fig = px.bar(dict1, x='Genres', y='Count')
    return fig.show()


q_books['score'] = q_books.apply(weighted_rating, axis=1)
q_books = q_books.sort_values('score', ascending=False)
q_books['genres'] = q_books['genres'].apply(get_list)
data['genres'] = data['genres'].apply(get_list)

features = ['author', 'genres']
for feature in features:
    q_books[feature] = q_books[feature].apply(clean_data)

q_books = q_books.reset_index(drop=True)
q_books["sim_score"] = 0 

titles = []

userInput = 1
print("Enter 's' to exit")
while userInput:
    val = input("Add book: ")
    if val == 's':
        break
    titles.append(val)
    


pd.set_option('display.max_columns', None)
r_books = recomend_books(q_books, titles)
print(r_books)