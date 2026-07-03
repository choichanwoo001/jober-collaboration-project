package com.example.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.Setter;

import java.util.List;

@Getter
@Setter
@lombok.experimental.Accessors(chain = true)
public class TemplateSaveRequestDto {
    @JsonProperty("templateId")
    private Long templateId;

    @JsonProperty("templateContent")
    private String templateContent;
    
    @JsonProperty("templateTitle")
    private String templateTitle;
    
    @JsonProperty("variableList")
    private List<VariableDto> variableList;
    
    @JsonProperty("category")
    private String category;
    
    @JsonProperty("buttonText")
    private String buttonText;
    
    @JsonProperty("userMessage")
    private String userMessage;
}
