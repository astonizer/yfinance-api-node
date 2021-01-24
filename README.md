# yfinance-api-node

An API endpoint which returns yahoo finance data in json format
<br>
Useful when the stack you use doesn't have a pre-written library for fetching yahoo finance data
<br>
<br>
`yfinance` python module was used for this feature

# Usage

In javascript(using axios)

    const stock_details = [
        {
            "Name": "Resonance Speci.",
            "Symbol": "RESONANCE.BO"
        },
        {
            "Name": "Tyche Industries",
            "Symbol": "TYCHE.BO"
        },
        ...
    ]
    
    axios({
        method: 'POST',
        url: 'https://yfinance-node.herokuapp.com/stocks',
        data: stock_details
    })
    .then(response => {
        console.log(response);

        // do something with the response
    })
    .catch(err => {
        console.error(err);
    });

[Example Project](https://github.com/astonizer/investment-planner)
