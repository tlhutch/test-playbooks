# Allow Use of Always Nodes In Conjuction With Other Workflow Job Template Nodes

### Feature Summary

Tower 3.4.0 relaxes the restrictions around use of "always" type nodes in
workflow job templates. Now they may be used in conjunction with "success" and
"failure" nodes.

### Related information

* [AWX Ticket](https://github.com/ansible/awx/issues/2255)
* [tower-qa ticket](https://github.com/ansible/tower-qa/issues/2208)

### Test case prerequisites

    N/A

### Test suites and cases
* [x] API
    * [x] Ensure always nodes can be used in conjunction with success and failure.
    * [x] A workflow job template node can add both a success and always node
    * [x] A workflow job template node can add both a failure and success node
    * [x] A workflow job template can add all three types of child nodes
    * [x] A workflow job template can run with all three types of child nodes
    * [x] Ensure cannot create cycles using the nodes that include both always and success / failure triggers

* [ ] [UI](https://docs.google.com/document/d/1vFMFURqFRv8T2wMA-AnUZQM0sNQcdTvwD_snUfwhKCQ/edit#heading=h.ht0fd5ex1upr)
