package sonicwall

import (
	"context"
	"encoding/json"
	"fmt"
	"net/url"
	"strings"

	"github.com/gandiva-tech/sonicwall-sdk/go/models"
)

const serviceObjectsBase = "/service-objects"

// ServiceObjectsService provides CRUD for service objects.
type ServiceObjectsService struct {
	client *Client
}

func isServiceObjectsSchemaArrayErr(err error) bool {
	if err == nil {
		return false
	}
	msg := strings.ToLower(err.Error())
	return strings.Contains(msg, "schema validation error") &&
		strings.Contains(msg, "service_objects") &&
		strings.Contains(msg, "expected '['")
}

// List returns all service objects.
func (s *ServiceObjectsService) List(ctx context.Context) ([]*models.ServiceObject, error) {
	data, err := s.client.request(ctx, "GET", serviceObjectsBase, nil)
	if err != nil {
		return nil, err
	}
	var top map[string]any
	if err := json.Unmarshal(data, &top); err != nil {
		return nil, err
	}
	raw, ok := top["service_objects"].([]any)
	if !ok {
		return nil, nil
	}
	out := make([]*models.ServiceObject, 0, len(raw))
	for _, it := range raw {
		m, ok := it.(map[string]any)
		if !ok {
			continue
		}
		o, err := models.ServiceObjectFromAPIItem(m)
		if err != nil {
			continue
		}
		out = append(out, o)
	}
	return out, nil
}

// Get returns a service object by name.
func (s *ServiceObjectsService) Get(ctx context.Context, name string) (*models.ServiceObject, error) {
	path := fmt.Sprintf("%s/name/%s", serviceObjectsBase, url.PathEscape(name))
	data, err := s.client.request(ctx, "GET", path, nil)
	if err == nil {
		var top map[string]any
		if err := json.Unmarshal(data, &top); err != nil {
			return nil, err
		}
		norm := normalizeGetFromPlural(top, "service_objects", "service_object", func(item map[string]any) bool {
			if so, ok := item["service_object"].(map[string]any); ok && so["name"] == name {
				return true
			}
			return item["name"] == name
		})
		return models.ServiceObjectFromAPIItem(norm)
	}

	if !IsNotFound(err) {
		return nil, err
	}

	list, err := s.List(ctx)
	if err != nil {
		return nil, err
	}
	for _, o := range list {
		if o.Name == name {
			return o, nil
		}
	}
	return nil, &NotFoundError{HTTPError{
		StatusCode:     404,
		SonicWallError: SonicWallError{message: "service object not found: " + name},
	}}
}

// Create creates a service object.
func (s *ServiceObjectsService) Create(ctx context.Context, obj *models.ServiceObject) (*models.ServiceObject, error) {
	payload := models.ServiceObjectToAPIEnvelope(obj)
	if err := s.client.post(ctx, serviceObjectsBase, payload, nil); err != nil {
		if !isServiceObjectsSchemaArrayErr(err) {
			return nil, err
		}
		if err := s.client.post(ctx, serviceObjectsBase, models.ServiceObjectCollectionPayload(obj), nil); err != nil {
			if err2 := s.client.post(ctx, serviceObjectsBase, models.ServiceObjectFirmwareCollectionPayload(obj), nil); err2 != nil {
				return nil, err2
			}
		}
	}
	got, gErr := s.Get(ctx, obj.Name)
	if gErr == nil {
		return got, nil
	}
	return obj, nil
}

// Update updates a service object.
func (s *ServiceObjectsService) Update(ctx context.Context, name string, obj *models.ServiceObject) (*models.ServiceObject, error) {
	path := fmt.Sprintf("%s/name/%s", serviceObjectsBase, url.PathEscape(name))
	payload := models.ServiceObjectToAPIEnvelope(obj)
	if err := s.client.put(ctx, path, payload, nil); err != nil {
		if !isServiceObjectsSchemaArrayErr(err) {
			return nil, err
		}
		if err := s.client.put(ctx, path, models.ServiceObjectCollectionPayload(obj), nil); err != nil {
			if err2 := s.client.put(ctx, path, models.ServiceObjectFirmwareCollectionPayload(obj), nil); err2 != nil {
				return nil, err2
			}
		}
	}
	got, gErr := s.Get(ctx, obj.Name)
	if gErr == nil {
		return got, nil
	}
	return obj, nil
}

// Delete removes a service object.
func (s *ServiceObjectsService) Delete(ctx context.Context, name string) error {
	path := fmt.Sprintf("%s/name/%s", serviceObjectsBase, url.PathEscape(name))
	return s.client.del(ctx, path)
}

// Ensure creates or updates a service object.
func (s *ServiceObjectsService) Ensure(ctx context.Context, obj *models.ServiceObject) (*models.ServiceObject, bool, error) {
	_, err := s.Get(ctx, obj.Name)
	if err != nil {
		if IsNotFound(err) {
			created, cErr := s.Create(ctx, obj)
			return created, true, cErr
		}
		return nil, false, err
	}
	updated, err := s.Update(ctx, obj.Name, obj)
	return updated, false, err
}
