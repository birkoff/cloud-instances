/// <reference types="Cypress" />

context('Actions', () => {
  beforeEach(() => {
    cy.visit('http://test-domain.dev/?account=engineering&region=frankfurt')
  })

  it('.click() - click on a DOM element', () => {
    	// https://on.cypress.io/click
    	cy.get('#instancesList > table > tbody > tr > td.text-left > button.changeStateButton.btn.btn-danger.btn-sm.terminate').click({force: true, multiple: true})
	})
})