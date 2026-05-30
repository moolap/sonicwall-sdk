package tech.gandiva.sonicwall.model;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

@JsonIgnoreProperties(ignoreUnknown = true)
public class SonicOsResponse {
  @JsonProperty("status")
  public Status status;

  @JsonIgnoreProperties(ignoreUnknown = true)
  public static class Status {
    public boolean success;
    public List<Info> info;
  }

  @JsonIgnoreProperties(ignoreUnknown = true)
  public static class Info {
    public String level;
    public int code;
    public String message;
  }
}
