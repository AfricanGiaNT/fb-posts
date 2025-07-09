# Phase 2 Testing Plan - Context-Aware AI System

## 🎯 Test Objectives
Verify that all Phase 2 context-aware features are working correctly:
- Context-aware prompting templates
- 6 relationship types with specific strategies
- Reference generation logic
- Enhanced AI generator with session context
- Content variation strategies
- Series continuity logic

## 📋 Test Scenarios

### Test 1: Initial Post Generation
**Goal**: Verify basic generation still works
**Steps**:
1. Upload a markdown file about a project
2. Verify post generates with one of the 5 tones
3. Approve the post
4. Check that it saves to Airtable with series tracking

**Expected Results**:
- Post generates successfully
- Tone selection is appropriate
- Series ID is created
- Post saved with sequence number 1

### Test 2: Context-Aware Second Post
**Goal**: Test context-aware generation for follow-up posts
**Steps**:
1. After approving first post, click "Generate Another Post"
2. Verify AI uses session context and previous post
3. Check for natural references to previous post
4. Verify different tone/approach is used

**Expected Results**:
- Post references previous post naturally ("In my last post...", "Building on what I shared...")
- Different tone or approach from first post
- Content shows awareness of previous post content
- Series continuity maintained

### Test 3: Relationship Type Functionality
**Goal**: Verify relationship types work correctly
**Steps**:
1. Generate 3-4 posts from same markdown file
2. Observe relationship type suggestions
3. Verify each relationship type produces different content strategies

**Expected Results**:
- Each post uses different relationship type
- Content varies based on relationship type
- References are appropriate for relationship type
- No repetition of content approaches

### Test 4: Reference Generation Logic
**Goal**: Test natural post-to-post references
**Steps**:
1. Generate multiple posts in sequence
2. Check for natural transition phrases
3. Verify references make sense contextually

**Expected Results**:
- Posts contain phrases like "In my last post...", "Building on what I shared..."
- References are contextually appropriate
- Flow between posts feels natural
- No awkward or forced references

### Test 5: Content Variation Strategies
**Goal**: Ensure posts don't repeat content
**Steps**:
1. Generate 5+ posts from same markdown file
2. Compare content focus and approach
3. Verify no repetition of key points

**Expected Results**:
- Each post focuses on different aspects
- No repetition of main points
- Varied perspectives and angles
- Content remains fresh and engaging

## 🔍 What to Look For

### ✅ Success Indicators
- Natural references between posts
- Different tones/approaches for each post
- No content repetition
- Contextually appropriate relationships
- Series tracking in Airtable
- Chat history preserved for approved posts

### ❌ Failure Indicators
- Posts don't reference each other
- Repetitive content or approaches
- Forced or awkward references
- Same tone used repeatedly
- Series tracking not working
- Context not being used by AI

## 🧪 Test File Suggestion
Use a markdown file about a recent project that has multiple aspects to discuss:
- Technical implementation
- Problem it solves
- User experience
- Lessons learned
- Future improvements

This will give the AI plenty of different angles to work with.

## 📊 Test Results Tracking

### Test 1: Initial Post Generation
- [ ] Post generated successfully
- [ ] Appropriate tone selected
- [ ] Series ID created
- [ ] Saved to Airtable correctly

### Test 2: Context-Aware Second Post
- [ ] Natural references to previous post
- [ ] Different tone/approach used
- [ ] Context awareness demonstrated
- [ ] Series continuity maintained

### Test 3: Relationship Type Functionality
- [ ] Different relationship types used
- [ ] Content strategies vary appropriately
- [ ] No repetition of approaches
- [ ] Suggestions make sense

### Test 4: Reference Generation Logic
- [ ] Natural transition phrases used
- [ ] References contextually appropriate
- [ ] Flow between posts feels natural
- [ ] No forced references

### Test 5: Content Variation Strategies
- [ ] Each post focuses on different aspects
- [ ] No repetition of main points
- [ ] Varied perspectives maintained
- [ ] Content remains fresh

## 🚀 Next Steps After Testing
Once all tests pass:
1. Document any issues found
2. Fix any problems identified
3. Proceed to Phase 3 implementation
4. Update project plan with test results

---

*Test Date: [DATE]*
*Tester: [NAME]*
*Results: [PASS/FAIL]* 