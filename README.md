# Survey - Token

### Use-Case:
Have you ever filled a survey or review and not been rewarded for it? With Survey token we remove the middleman like SurveyMonkey and G2Crowd and redistribute the money to people taking the survey and adding reviews. Survey Monkey is a billion dollar company and G2 Crowd is funded with 45M dollars. Very few surveyers/ reviewers are  rewarded in coupons. With Survey token running on NEO, we incentivize surveyers with SUR token. SUR tokens are bought by the survey lister. 

### Stack

 - Smart Contract: https://github.com/melvin0008/survey-token
 - Frontend: https://github.com/melvin0008/survey-frontend
 - Backend: https://github.com/melvin0008/survey-backend


### Dapp Usage:

CozNet Hash: 0xd4903b35332d2a652f126ea6a978c179994321b3

## Functions available:
Name, symbol, balanceOf, transfer, transferFrom, totalSupply and other NEX template functions.

Since this is a market place where in there are two sides.
 - Surveyer
 - Survey Lister

*After importing token to wallet*

The person creating the survey will invoke the function 

`testinvoke 0xd4903b35332d2a652f126ea6a978c179994321b3 create_survey  [“<survey_id>”, <number_of_people to distribute to>] --attach-gas=<GAS that will be redistributed>`

Survey Id: The id of the survey with question. 
Number of people to distribute the assets

`testinvoke 0xd4903b35332d2a652f126ea6a978c179994321b3 reward  [“<survey_id>”, <address of surveyer>]`

address of surveyer : will be the address of the person who will be rewarded. 
