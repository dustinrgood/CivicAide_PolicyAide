# CivicAide Development Memory

## 2024-08-17: Policy Comparison Preservation Ideas

### Issue Identified
The current policy tournament system generates rich comparative analyses between policy proposals, but much of this valuable data is lost in the final report. The report only shows the "winners" without preserving the nuanced reasoning behind why certain policies were preferred over others.

### Proposed Improvements
1. **Intermediate Artifacts**: Generate intermediate documents like "Detailed Policy Comparison Analysis" or "Full Tournament Results" that preserve the rich comparison data.

2. **Multi-level Reporting**: Create tiered reports with:
   - Executive summary for high-level decision makers
   - Detailed appendices with full comparison analyses for stakeholders who want deeper insights
   - Technical documentation of the evolution process

3. **Traceability**: Add citations or references in the final report linking back to specific comparison analyses (e.g., "Policy A was preferred over Policy B due to economic feasibility - see Comparison #4").

4. **Interactive Reporting**: If delivered through a web interface, make sections expandable to reveal the detailed comparisons behind conclusions.

5. **Process Visualization**: Include a visualization of the tournament process showing how policies competed and evolved, with access to the full comparison reasoning.

6. **Comparison Data Preservation**: Modify report generation to extract and incorporate important insights from each comparison rather than reducing everything to a simple "superior policy" statement.

### Implementation Considerations
- Store all policy comparisons in a structured format during the tournament process
- Enhance the `_run_tournament` method to save detailed comparison results
- Modify `_create_final_report` to reference and incorporate saved comparison data
- Consider adding a "tournament_history" field to the FinalReportModel

## 2024-08-17: Web Search Enhancement

### Issue Identified
The policy evolution system was making simulated web searches instead of real API calls. Logs showed that while the OpenAI web search tool was being called in the dashboard, the custom web search in our code wasn't connecting to an actual search API for over 10 hours.

### Root Cause Analysis
1. The `web_search_api` function in `policy_evolution.py` was designed to use SerpAPI for web searches
2. The `SERP_API_KEY` environment variable was missing from the `.env` file
3. Without the API key, the system was falling back to simulated mock results with generic placeholders
4. This resulted in less specific and relevant policy recommendations

### Implemented Fixes
1. Enhanced the `web_search_api` function with a two-tier approach:
   - Primary: Use SerpAPI if the API key is available (requires adding key to local.env)
   - Secondary: Use OpenAI's built-in web search tool when SerpAPI is unavailable
   - Last resort: Fall back to simulated results only if both methods fail

2. Added better logging throughout the search process:
   - Clear indication of which search method is being used
   - Error reporting for search API issues
   - Warnings when falling back to simulated results

3. Improved result formatting:
   - Standardized result format regardless of search method used
   - Extract URLs and content from OpenAI web search results
   - Limited results to top 3 to maintain consistency

### Current Status
- Web searches now use real data by default through OpenAI's web search tool
- System can also use SerpAPI if configured with an API key
- The policy recommendations should be more specific, current, and relevant
- Added instructions in local.env for how to add a SerpAPI key for even better search results

### Next Steps
1. Monitor web search usage and result quality
2. Consider adding caching for search results to avoid duplicate searches
3. Implement better parsing of search results to extract more structured data
4. Explore adding more specialized search queries based on policy topics

## 2024-03-18: Local Context Passing Fix

### Issue Identified
We discovered that in some runs of the policy evolution system, the local context information wasn't being properly passed to the OpenAI API. This resulted in generic policy recommendations that didn't reference the specific jurisdiction or local context details provided by the user.

For example:
- In earlier runs (ban_ban_2), the output was appropriately localized with explicit references to "Elgin, Illinois" and its "strong arts community"
- In recent runs (bag_ban_3), the output was more generic and didn't reference the specific jurisdiction

### Root Cause Analysis
1. The local context was being gathered correctly through user inputs
2. However, the context wasn't being emphasized strongly enough in the prompts
3. There was no verification mechanism to check if the generated content referenced the local context
4. When using the orchestration pattern with parallel processes, context may not have been properly shared

### Implemented Fixes
1. Added debug logging throughout the code to track context at key points:
   - After gathering local context
   - Before generating policy proposals
   - Before creating the final report
   - At the start of orchestration processes

2. Enhanced the policy generation prompt:
   - Made local context more prominent with clear section headers and ALL CAPS
   - Added explicit instructions to reference the specific jurisdiction
   - Included more context details in the prompt (demographics, prior attempts)

3. Added a context verification mechanism:
   - Added code to check if proposals reference the jurisdiction
   - If not, added stronger instructions to ensure the final report is localized
   - Used uppercase jurisdiction name to emphasize importance

4. Improved final report generation:
   - Added special instructions when context isn't properly referenced
   - Extended local context information in prompts
   - Added explicit direction to tailor all sections to local context

### Current Status
- The system now has robust debugging to track context flow
- Prompts are structured to strongly emphasize local context
- A verification step ensures localization in the final report
- Parallel processes in orchestration now properly pass context

### Next Steps
1. Test the system with various jurisdictions to verify consistent localization
2. Consider adding explicit examples in prompts to demonstrate proper localization
3. Add metrics to track the degree of localization in generated content
4. Explore additional ways to strengthen context preservation in the multi-model orchestration pattern

## 2024-03-18: Stakeholder Influence Validation Fix

### Issue Identified
When users entered additional context information in the "Would you like to provide detailed stakeholder influence information?" prompt instead of just "yes" or "no", the system failed to create a valid LocalContext object due to validation errors with the stakeholder_influence field.

Error message:
```
Error creating local context: 1 validation error for LocalContext
stakeholder_influence
  Input should be a valid dictionary [type=dict_type, input_value='Not specified', input_type=str]
```

This caused the system to fall back to default "Not specified" values for all context fields, effectively losing the user's input data.

### Root Cause Analysis
1. The stakeholder_influence field was being set to the user's text input instead of maintaining it as a dictionary
2. The error handling wasn't robust enough to recover from validation failures
3. The fallback mechanism completely discarded user input instead of preserving what it could

### Implemented Fixes
1. Modified the stakeholder_influence handling:
   - Always initialize it as an empty dictionary
   - Only populate it when the user explicitly types "yes"
   - For other inputs, store the text in a new contextual_notes field

2. Added the contextual_notes field to the LocalContext class to preserve additional context

3. Improved error handling with a three-tier approach:
   - First try: create the LocalContext with the user's input
   - Second try: fix common validation issues and try again
   - Last resort: manually create a context object preserving as much input data as possible

4. Added more granular debug logging to track what's happening during the context creation process

### Current Status
- The system now properly handles free-text input in the stakeholder influence prompt
- User context information is preserved even when validation issues occur
- Multiple fallback mechanisms ensure we never lose input data
- Debug logging helps track the context creation process

### Next Steps
1. Add more comprehensive input validation for all context fields
2. Consider using a more structured form-like interface for context gathering
3. Add examples of expected input format for each field
4. Consider adding a review step where users can verify their context information before proceeding

## 2024-03-19: Policy Comparison Enhancement

### Issue Identified
The policy tournament system was comparing proposals using only their IDs rather than full text content. This limited the quality of comparisons and potentially led to less accurate policy rankings.

### Root Cause Analysis
1. The `_compare_proposals` method was receiving only proposal IDs
2. The model couldn't evaluate the actual content of proposals
3. This led to potentially superficial comparisons based on limited information

### Implemented Fixes
1. Modified `_compare_proposals` to use full proposal text:
   - Now receives complete policy text instead of just IDs
   - Includes title, description, rationale, and implementation details
   - Allows for deeper, more nuanced comparisons

2. Enhanced winner determination:
   - Matches returned text with original proposal texts
   - Explicitly calculates winner and loser IDs
   - Updates Elo ratings with clear winner/loser identification

3. Improved traceability:
   - Added proper trace ID and round span ID tracking
   - Ensures token usage and OpenAI response IDs are properly recorded
   - Maintains better audit trail of comparison decisions

### Impact
- Higher quality policy comparisons due to full context evaluation
- More accurate Elo ratings based on detailed analysis
- Better traceability of decision-making process
- Increased processing time and token usage, but justified by improved quality

### Current Status
- System now performs full-text comparisons
- Processing time increased but quality improved
- Better tracking of comparison reasoning
- More accurate policy evolution results

### Next Steps
1. Monitor comparison quality metrics
2. Consider adding comparison reasoning to final reports
3. Evaluate potential optimizations while maintaining quality
4. Add logging for comparison quality assessment 