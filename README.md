# What2Eat(머먹?)

What2Eat is a chatbot-style application that helps you find highly-rated restaurants based on user reviews and ratings from Kakao Map.

## 🍽️ About the Project

What2Eat analyzes over 1 million reviews from 46,000+ restaurants in Seoul to provide personalized restaurant recommendations. The project uses a unique algorithm to identify "meaningful positive reviews" and "meaningful negative reviews" to give users a more accurate picture of a restaurant's quality.

### Key Features:

- Chatbot interface for easy interaction
- Recommendations based on location and food preferences
- Analysis of "Jjup Jjup Doctors" (쩝쩝박사) - users who gave higher than their average ratings
- Warning system for restaurants with high "non-favorable" percentages

## 🚀 Getting Started

You can access What2Eat through the following links:

- [What2Eat Chat Version](https://what2eat-chat.streamlit.app/)
- [What2Eat Map Version](https://what2eat.streamlit.app/)
- [What2Eat LLM Version](https://laas.wanted.co.kr/sandbox/share?project=PROMPTHON_PRJ_463&hash=f11097aa25dde2ef411ac331f47c1a3d1199331e8c4d10adebd7750576f442ff)

## 🛠️ Built With

- Python
- Streamlit
- Kakao Map API

## 📊 How It Works

1. **Data Collection**: Over 1 million reviews from 46,000+ Seoul restaurants were collected from Kakao Map.

2. **Review Analysis**: 
   - Positive reviews: Identified when a user rates a restaurant higher than their personal average.
   - Negative reviews: Flagged when a user with an average rating of 3.5+ gives a restaurant 1.5 stars or less.

3. **Ranking System**:
   - "Jjup Jjup Doctors" (쩝쩝박사): Number of meaningful positive reviewers
   - "Jjup Jjup Percent" (쩝쩝퍼센트): (Number of meaningful positive reviewers / Total reviewers) * 100

4. **Display Criteria**:
   - Restaurants with more than 5 "Jjup Jjup Doctors" are ranked by "Jjup Jjup Percent"
   - Warnings are displayed for restaurants with over 10% meaningful negative reviews

## 📝 Blog Post

For more detailed information about the development process and methodologies, check out our [blog post](https://learningnrunning.github.io/example/tech/review/2024-03-03-From-KakaoRok-to-What2Eat/).

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/YourGitHubUsername/What2Eat/issues).

## 📫 Contact

Your Name - [Your Email]

Project Link: [https://github.com/YourGitHubUsername/What2Eat](https://github.com/YourGitHubUsername/What2Eat)

## 🙏 Acknowledgements

- [Kakao Map](https://map.kakao.com/) for providing the initial data
- All the food lovers who contributed reviews and ratings