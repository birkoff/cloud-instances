/// <reference types="Cypress" />

var name_prefix = (new Date).valueOf()
context('Actions', () => {
	it('.type() - type into a DOM element', () => {
		cy.visit('http://test-domain.dev/?account=engineering&region=frankfurt')
		.then(function () {
		    cy.get('#instancesList > table > tbody > tr > td.text-left > button.changeStateButton.btn.btn-danger.btn-sm.update').first().click()
//			cy.get('#instanceModalButton').click()
//			cy.get('#create-name')
//				.type('cypress-ent-to-end-test-' + name_prefix, { delay: 100 })
//				.should('have.value', 'cypress-ent-to-end-test-' + name_prefix)
//
//			cy.get('#create-owner').select('hector')
//
//			cy.get('#create-image-id')
//				.type('ami-0151d8654227898e7', { delay: 100 })
//				.should('have.value', 'ami-0151d8654227898e7')
//
//
//			cy.get('#create-terminate-date')
//			cy.get('#create-instance').click()
//			cy.get('.alert.alert-success').should('be.visible')
		})
	})
})