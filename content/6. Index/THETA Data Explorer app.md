> Many thanks to M D Madhusudan, [Akshay S Dinesh](https://learnlearn.in/about/) and Nandini Velho for fundamental conceptual help when I was early stage conceptualising this work in 2017-18 & for continous support in various aspects of this work as it continues to unfold. Full list of people involved are listed either as co-authors or under acknowledgements of the THETA Protocol ([link](https://wellcomeopenresearch.org/articles/4-202))

As part of the [[THETA|Towards Health Equity and Transformative Action on Tribal Health (THETA) project]], we have generated a fairly large and complex dataset that includes settlements, households, and individual level data, across five sites (proteted areas) in four states in southern, central & NE India. The data spans demography, livelihoods, household conditions, maternal and child health, nutrition, non-communicable diseases, and health system interactions. 
  
The full dataset is archived on [Figshare](https://doi.org/10.6084/m9.figshare.23701863.v1). But to enable ongoing engagement by others while I continue makign sense of the full dataset, thogut of trying out a way of allowing people to easily query/engage with the data so this is notes for that effort. 

The key is to allow meaningful exploration without flattenign the 3-level (individual data, household level data & village level data). 
  
I’ve now set up a first working version of a [THETA-specific public data exploration app](https://theta-data-explorer.streamlit.app) using Streamlit, hosted on Streamlit Community Cloud:

**👉 https://theta-data-explorer.streamlit.app/**

At this stage, the app is barely set up....still ironing out the kinks and testing. Hopefully the data will start speaking...and perhaps even tell a story....a story that perhaps [answers the question posed here in the protocol](https://wellcomeopenresearch.org/articles/4-202).


Right now, the app allows a user to:

- Load structured tabular data through a browser
- Filter variables interactively (categorical, numeric, boolean)
- Subset the data without writing any code
- Download filtered slices for further analysis
- See the deployment and code transparently via GitHub


The data is structured across three linked levels:

1. Settlement-level data
    Unit of analysis: village / settlement
    Key: deidentified_village
    
2. Household-level data
    Unit of analysis: household
    Keys: deidentified_village, fulcrum_id_parent
    
3. Individual-level data
    Unit of analysis: person
    Keys: fulcrum_id_people, fulcrum_id_parent


The next iteration of the THETA data explorer will reflect this structure much more explicitly.

1. Separate views for each dataset: The app will be organised into three sections (likely as tabs):

	- Settlements – village-level characteristics and context
	- Households – socio-economic conditions and household-level variables
	- Individuals – MCH, nutrition, NCDs, behaviours, anthropometry

2. Multi-level exploration

It should be possible to:
	- explore households within a selected settlement, or
	- explore individuals within selected households,

### Current status

- ✅ Public Streamlit app deployed
- ✅ Reproducible GitHub → Streamlit deployment 
- ==🔄 Work in progress on dataset-specific views==
.....

---
Last updated: 2025-12-30 16:03
