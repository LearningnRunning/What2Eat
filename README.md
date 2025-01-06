# What2Eat(머먹?)


## 🍽️ About the Project
**What2Eat** is a smarter way to rank restaurants, moving beyond simple averages and review counts. By incorporating reviewer traits, recency, and subjective biases, it calculates more reliable and nuanced scores to identify the best dining spots.

### Key Features:

- Chatbot interface for easy interaction
- Recommendations based on location and food preferences
- **Personalized Adjustments**: Scores reflect reviewer habits, recency, and credibility.
- **Robust Rankings**: Bayesian adjustments reduce the impact of outliers and small sample sizes.
- **Manipulation-Resistant**: Incorporates reviewer activity to mitigate spam or biased reviews.

## 🚀 Getting Started

You can access What2Eat through the following links:

- [What2Eat Chat Version](https://what2eat-chat.streamlit.app/)
<!-- - [What2Eat Map Version](https://what2eat.streamlit.app/) -->
- [What2Eat LLM Version](https://laas.wanted.co.kr/sandbox/share?project=PROMPTHON_PRJ_463&hash=f11097aa25dde2ef411ac331f47c1a3d1199331e8c4d10adebd7750576f442ff)

## 🛠️ Built With

- Python
- Streamlit
- Kakao Map API

## 📊 How It Works

1. **Data Collection**: Over 1.5 million reviews from 1,650,000+ Seoul restaurants were collected from Kakao Map.
   - Data includes reviewer ID, scores, review text, timestamps, and additional metadata like reviewer badges or levels.

2. **Review Analysis**: 
   - Each review is evaluated using three factors:
     - **Reviewer Bias**: How a review’s score compares to the reviewer’s typical scoring pattern (`score_scaled`).
     - **Recency**: Reviews written within the last 3 months are weighted higher, with older reviews gradually losing weight (`date_scaled`).
     - **Reviewer Credibility**: Reviewers with higher activity levels or badges receive more influence (`badge_scaled`).
   - These factors are normalized and combined into a **Combined Score** for each review.

3. **Ranking System**:
   - **Individual Review Aggregation**:
     - Reviews for each restaurant are combined using **Bayesian Adjusted Averages**, ensuring restaurants with fewer reviews are not unfairly overrepresented.
   - **Final Score Calculation**:
     \[
     \text{Restaurant Score} = \frac{(\mu \times k) + (x} \times N)}{k + N}
     \]
     - \( \mu \): Average of all restaurants’ combined scores.
     - \( k \): Minimum review count threshold (e.g., 5).
     - \( x \): Restaurant’s average combined score.
     - \( N \): Number of reviews for the restaurant.
   
4. **Display Criteria**:
   - Restaurants are ranked by their **Bayesian Adjusted Scores**.
   - Additional filters include:
     - **Cuisine Type**: Narrow down results by category (e.g., Korean, Italian, Cafes).
     - **Location**: Filter by specific areas or neighborhoods.
   - Warnings are displayed for restaurants with over 10% meaningful negative reviews

## 📝 Blog Post

For more detailed information about the development process and methodologies, check out our [blog post](https://learningnrunning.github.io/post/tech/review/2024-12-30-Aggregate-restaurant-ratings-data/).

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/learningnrunning/What2Eat/issues).

## 📫 Contact

Seongrok Kim- [max_sungrok@naver.com]

Project Link: [https://github.com/learningnrunning/What2Eat](https://github.com/learningnrunning/What2Eat)

## 🙏 Acknowledgements

- [Kakao Map](https://map.kakao.com/) for providing the initial data
- All the food lovers who contributed reviews and ratings