// Copyright (c) 2026, Solidad Kimeu and contributors
// For license information, please see license.txt

frappe.ui.form.on("Quickflow SMS Settings", {
	top_up(frm) {
		let d = new frappe.ui.Dialog({
			title: __("Top Up"),
			fields: [
				{
					label: __("Phone Number"),
					fieldname: "mobile",
					fieldtype: "Data",
					reqd: 1,
				},
				{
					label: __("Amount"),
					fieldname: "amount",
					fieldtype: "Currency",
					reqd: 1,
				},
			],
			primary_action_label: __("Top Up"),
			primary_action(values) {
				d.hide();
				frappe.call({
					method: "quickflow_sms.services.rest.initiate_payment",
					args: {
						mobile: values.mobile,
						amount: values.amount,
					},
					callback: function (r) {
						if (r.message && r.message.ResponseCode === "0") {
							frappe.msgprint(
								__("STK Push initiated successfully. Please check your phone.")
							);
						} else if (r.message && r.message.CustomerMessage) {
							frappe.msgprint({
								title: __("Payment Status"),
								message: r.message.CustomerMessage,
								indicator: "blue",
							});
						}
					},
				});
			},
		});

		d.show();
	},
});
