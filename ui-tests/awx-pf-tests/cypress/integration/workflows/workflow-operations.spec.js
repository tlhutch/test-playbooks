/*
 * Basic operations on workflows and the workflow visualizer.
 */

context.skip('Workflow visualizer operations', function() {
  it('Can make a regular workflow', function() {})
  it('Can edit a workflow', function() {})
  it('Can delete a workflow node', function() {})
  context('Convergence nodes', function() {
    it('Can converge a workflow', function() {})
    it('Can run expected convergence node logic', function() {})
    it('Can can deconverge a workflow', function() {})
  })
  it('Fails a recursive workflow', function() {})
  it('Can create a regular workflow-within-workflow', function() {})
  it('Can verify a pass and fail node', function() {})
  it('Can verify that the first node is an always node', function() {})
  context('Approval nodes', function() {
    it('Can run expected approval node logic', function() {})
    it('Can view approval node notifications', function() {})
  })
})
