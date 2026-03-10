package com.example.controller;

import org.zkoss.zk.ui.Component;
import org.zkoss.zk.ui.select.SelectorComposer;
import org.zkoss.zk.ui.select.annotation.Wire;
import org.zkoss.zk.ui.select.annotation.Listen;
import org.zkoss.zul.*;

public class MyComposer extends SelectorComposer<Component> {

    @Wire
    private Textbox nameInput;

    @Wire
    private Button submitBtn;

    @Override
    public void doAfterCompose(Component comp) throws Exception {
        super.doAfterCompose(comp);
        // Initialization logic
    }

    @Listen("onClick = #submitBtn")
    public void onSubmit() {
        String name = nameInput.getValue();
        // Handle submit
    }
}